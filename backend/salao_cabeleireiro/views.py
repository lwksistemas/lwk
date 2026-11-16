"""API do salão: cadastros, agenda no formato da clínica e painel fixo da loja."""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agenda_service import conflito_horario, interpretar_inicio
from .caixa_service import comissao_do_atendimento, gravar_comissoes, interpretar_formas, motivo_bloqueio_recebimento, quantia, rotulo_formas
from .comunicacao_service import avisar_mudanca, enviar_evento, regras_de, validar_regras, whatsapp_pronto
from .catalogo import garantir_catalogo_inicial
from .models import FORMAS_PAGAMENTO, PAINEIS, STATUS_AGENDAMENTO, STATUS_OCUPA_HORARIO, Agendamento, Bloqueio, Cliente, HorarioTrabalho, Profissional, Recebimento, SalaoConfig, Servico, Venda
from .loja_config import cores_gravadas
from .permissions import IsSalaoAdmin, IsSalaoMembro, contexto_salao, papel_salao, usuario_e_admin
from .serializers import AgendamentoSerializer, ClienteSerializer, ProfissionalSerializer, ServicoSerializer, painel_valido


class GetObjectMixin:
    model_class = None
    not_found_message = "Registro não encontrado"

    def object_or_404(self, pk):
        try:
            return self.model_class.objects.get(pk=pk), None
        except self.model_class.DoesNotExist:
            return None, Response({"error": self.not_found_message}, status=status.HTTP_404_NOT_FOUND)


def _erro(mensagem, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({"error": mensagem}, status=codigo)


MODELOS = {"recepcionista", "autonomo"}
LOCAIS = {"caixa", "agenda", "ambos"}


def _config():
    config = SalaoConfig.objects.first()
    if config is not None:
        return config
    return SalaoConfig.objects.create(painel="operacao")


def _abertura_do_caixa() -> str:
    from .models import SessaoCaixa

    sessao = SessaoCaixa.objects.filter(is_active=True).order_by("-aberta_em").first()
    if sessao is None:
        return ""
    return timezone.localtime(sessao.aberta_em).strftime("%d/%m/%Y %H:%M")


def _funcionamento(config, loja, prof, user):
    modelo = config.modelo if config.modelo in MODELOS else "recepcionista"
    local = config.local_recebimento if config.local_recebimento in LOCAIS else "caixa"
    nome = (user.get_full_name() or "").strip() or user.get_username()
    return {
        "modelo": modelo,
        "local_recebimento": local,
        "papel": papel_salao(loja, prof, user, modelo),
        "operador_nome": nome,
        "caixa_abertura": _abertura_do_caixa(),
    }


class ConfigView(APIView):
    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAuthenticated(), IsSalaoAdmin()]
        return [IsAuthenticated(), IsSalaoMembro()]

    def get(self, request):
        garantir_catalogo_inicial()
        loja, prof = contexto_salao(request)
        config = _config()
        return Response({
            "painel": config.painel,
            "paineis": [{"id": codigo, "nome": nome} for codigo, nome in PAINEIS],
            "pode_trocar": usuario_e_admin(loja, prof, request.user),
            **_funcionamento(config, loja, prof, request.user),
            **cores_gravadas(loja),
        })

    def put(self, request):
        painel = (request.data.get("painel") or "").strip()
        if not painel_valido(painel):
            return _erro("Escolha Operação do dia, Gestão do mês ou Agenda da semana.")
        config = _config()
        config.painel = painel
        config.save(update_fields=["painel"])
        return Response({"painel": config.painel, "pode_trocar": True})


class FuncionamentoView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def put(self, request):
        modelo = (request.data.get("modelo") or "").strip()
        local = (request.data.get("local_recebimento") or "").strip()
        if modelo not in MODELOS:
            return _erro("Escolha o salão com recepção ou o profissional autônomo.")
        if local not in LOCAIS:
            return _erro("Escolha onde o pagamento é recebido.")
        config = _config()
        config.modelo = modelo
        config.local_recebimento = local
        config.save(update_fields=["modelo", "local_recebimento"])
        loja, prof = contexto_salao(request)
        return Response(_funcionamento(config, loja, prof, request.user))


class ClienteListCreateView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Cliente

    def get(self, request):
        qs = Cliente.objects.filter(is_active=True).order_by("nome")
        busca = (request.query_params.get("q") or "").strip()
        if busca:
            qs = qs.filter(Q(nome__icontains=busca) | Q(telefone__icontains=busca))
        return Response(ClienteSerializer(qs[:200], many=True).data)

    def post(self, request):
        serializer = ClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cliente = serializer.save()
        return Response(ClienteSerializer(cliente).data, status=status.HTTP_201_CREATED)


class ClienteDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Cliente
    not_found_message = "Cliente não encontrado."

    def patch(self, request, pk):
        cliente, erro = self.object_or_404(pk)
        if erro:
            return erro
        serializer = ClienteSerializer(cliente, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ClienteSerializer(cliente).data)

    def delete(self, request, pk):
        cliente, erro = self.object_or_404(pk)
        if erro:
            return erro
        cliente.is_active = False
        cliente.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfissionalListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        qs = Profissional.objects.filter(is_active=True).prefetch_related("comissoes__servico").order_by("nome")
        return Response(ProfissionalSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ProfissionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profissional = serializer.save()
        try:
            gravar_comissoes(profissional, request.data.get("comissoes"))
        except ValueError as exc:
            return _erro(str(exc))
        for dia in range(6):
            HorarioTrabalho.objects.create(
                profissional=profissional,
                dia_semana=dia,
                hora_entrada=time(9, 0),
                hora_saida=time(19, 0),
            )
        return Response(ProfissionalSerializer(profissional).data, status=status.HTTP_201_CREATED)


class ProfissionalDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Profissional
    not_found_message = "Profissional não encontrado."

    def patch(self, request, pk):
        profissional, erro = self.object_or_404(pk)
        if erro:
            return erro
        serializer = ProfissionalSerializer(profissional, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        try:
            gravar_comissoes(profissional, request.data.get("comissoes") if "comissoes" in request.data else None)
        except ValueError as exc:
            return _erro(str(exc))
        return Response(ProfissionalSerializer(profissional).data)

    def delete(self, request, pk):
        profissional, erro = self.object_or_404(pk)
        if erro:
            return erro
        profissional.is_active = False
        profissional.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServicoListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        garantir_catalogo_inicial()
        qs = Servico.objects.filter(is_active=True).order_by("categoria", "nome")
        return Response(ServicoSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ServicoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        servico = serializer.save()
        return Response(ServicoSerializer(servico).data, status=status.HTTP_201_CREATED)


class ServicoDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Servico
    not_found_message = "Serviço não encontrado."

    def patch(self, request, pk):
        servico, erro = self.object_or_404(pk)
        if erro:
            return erro
        serializer = ServicoSerializer(servico, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ServicoSerializer(servico).data)

    def delete(self, request, pk):
        servico, erro = self.object_or_404(pk)
        if erro:
            return erro
        servico.is_active = False
        servico.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


def _cliente_do_payload(dados):
    cliente_id = dados.get("cliente") or dados.get("cliente_id")
    if cliente_id:
        cliente = Cliente.objects.filter(pk=cliente_id, is_active=True).first()
        if cliente is None:
            raise ValueError("Cliente não encontrado.")
        return cliente
    novo = dados.get("cliente_novo") or {}
    serializer = ClienteSerializer(data={
        "nome": novo.get("nome") or dados.get("cliente_nome"),
        "telefone": novo.get("telefone") or dados.get("cliente_telefone"),
    })
    if not serializer.is_valid():
        raise ValueError("Informe o cliente, com nome e telefone.")
    return serializer.save()


class AgendaView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        inicio = request.query_params.get("start")
        fim = request.query_params.get("end")
        qs = Agendamento.objects.select_related("cliente", "profissional", "servico").prefetch_related("recebimentos")
        try:
            if inicio:
                qs = qs.filter(inicio__gte=interpretar_inicio(inicio))
            if fim:
                qs = qs.filter(inicio__lte=interpretar_inicio(fim))
        except ValueError as exc:
            return _erro(str(exc))
        if not inicio and not fim:
            agora = timezone.now()
            qs = qs.filter(inicio__gte=agora - timedelta(days=7), inicio__lte=agora + timedelta(days=60))
        profissional = request.query_params.get("profissional")
        if profissional:
            qs = qs.filter(profissional_id=profissional)
        return Response(AgendamentoSerializer(qs.order_by("inicio")[:500], many=True).data)

    def post(self, request):
        try:
            inicio = interpretar_inicio(str(request.data.get("inicio") or ""))
        except ValueError as exc:
            return _erro(str(exc))
        servico = Servico.objects.filter(pk=request.data.get("servico"), is_active=True).first()
        profissional = Profissional.objects.filter(pk=request.data.get("profissional"), is_active=True).first()
        if servico is None or profissional is None:
            return _erro("Escolha o serviço e o profissional.")
        try:
            cliente = _cliente_do_payload(request.data)
        except ValueError as exc:
            return _erro(str(exc))
        duracao = int(request.data.get("duracao_minutos") or servico.duracao_minutos)
        fim = inicio + timedelta(minutes=duracao)
        mensagem = conflito_horario(profissional.id, inicio, fim)
        if mensagem:
            return _erro(mensagem, status.HTTP_409_CONFLICT)
        agendamento = Agendamento.objects.create(
            inicio=inicio,
            duracao_minutos=duracao,
            status="SCHEDULED",
            cliente=cliente,
            profissional=profissional,
            servico=servico,
            observacoes=(request.data.get("observacoes") or "").strip(),
        )
        return Response(AgendamentoSerializer(agendamento).data, status=status.HTTP_201_CREATED)


class AgendamentoDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Agendamento
    not_found_message = "Agendamento não encontrado."

    def get_object(self, pk):
        try:
            return Agendamento.objects.select_related("cliente", "profissional", "servico").prefetch_related("recebimentos").get(pk=pk)
        except Agendamento.DoesNotExist:
            return None

    def patch(self, request, pk):
        agendamento = self.get_object(pk)
        if agendamento is None:
            return _erro(self.not_found_message, status.HTTP_404_NOT_FOUND)
        if agendamento.recebimentos.filter(is_active=True).exists() and any(
            chave in request.data for chave in ("status", "inicio", "profissional", "servico", "duracao_minutos")
        ):
            return _erro("Desfaça o recebimento antes de alterar este atendimento.")
        inicio_anterior = agendamento.inicio
        status_anterior = agendamento.status
        status_novo = request.data.get("status")
        if status_novo:
            if status_novo not in {codigo for codigo, _ in STATUS_AGENDAMENTO}:
                return _erro("Status inválido.")
            agendamento.status = status_novo
        if request.data.get("inicio"):
            try:
                agendamento.inicio = interpretar_inicio(str(request.data.get("inicio")))
            except ValueError as exc:
                return _erro(str(exc))
        if request.data.get("profissional"):
            profissional = Profissional.objects.filter(pk=request.data.get("profissional"), is_active=True).first()
            if profissional is None:
                return _erro("Profissional não encontrado.")
            agendamento.profissional = profissional
        if request.data.get("servico"):
            servico = Servico.objects.filter(pk=request.data.get("servico"), is_active=True).first()
            if servico is None:
                return _erro("Serviço não encontrado.")
            agendamento.servico = servico
            if not request.data.get("duracao_minutos"):
                agendamento.duracao_minutos = servico.duracao_minutos
        if request.data.get("duracao_minutos"):
            agendamento.duracao_minutos = int(request.data.get("duracao_minutos"))
        if "observacoes" in request.data:
            agendamento.observacoes = (request.data.get("observacoes") or "").strip()
        if agendamento.status in STATUS_OCUPA_HORARIO:
            mensagem = conflito_horario(
                agendamento.profissional_id,
                agendamento.inicio,
                agendamento.fim,
                ignorar_id=agendamento.id,
            )
            if mensagem:
                return _erro(mensagem, status.HTTP_409_CONFLICT)
        agendamento.save()
        return _resposta_agenda(agendamento, avisar_mudanca(
            agendamento,
            inicio_anterior=inicio_anterior,
            status_anterior=status_anterior,
            user=request.user,
        ))

    def delete(self, request, pk):
        agendamento = self.get_object(pk)
        if agendamento is None:
            return _erro(self.not_found_message, status.HTTP_404_NOT_FOUND)
        if agendamento.recebimentos.filter(is_active=True).exists():
            return _erro("Desfaça o recebimento antes de cancelar este atendimento.")
        status_anterior = agendamento.status
        agendamento.status = "CANCELLED"
        agendamento.save(update_fields=["status", "updated_at"])
        return _resposta_agenda(agendamento, avisar_mudanca(
            agendamento,
            inicio_anterior=agendamento.inicio,
            status_anterior=status_anterior,
            user=request.user,
        ))


def _resposta_agenda(agendamento, aviso):
    dados = AgendamentoSerializer(agendamento).data
    if aviso:
        dados["aviso"] = aviso
    return Response(dados)


def _hora(valor, obrigatorio=False):
    texto = (str(valor or "")).strip()
    if not texto:
        if obrigatorio:
            raise ValueError("Informe o horário.")
        return None
    try:
        return datetime.strptime(texto[:5], "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Use o horário no formato HH:MM.") from exc


def _validar_dia_jornada(dia):
    ativo = bool(dia.get("ativo"))
    entrada = _hora(dia.get("hora_entrada"), obrigatorio=ativo) or time(9, 0)
    saida = _hora(dia.get("hora_saida"), obrigatorio=ativo) or time(19, 0)
    intervalo_inicio = _hora(dia.get("intervalo_inicio"))
    intervalo_fim = _hora(dia.get("intervalo_fim"))
    if ativo and entrada >= saida:
        raise ValueError("A saída precisa ser depois da entrada.")
    if bool(intervalo_inicio) != bool(intervalo_fim):
        raise ValueError("Informe o começo e o fim do intervalo.")
    if intervalo_inicio and intervalo_fim and not (entrada <= intervalo_inicio < intervalo_fim <= saida):
        raise ValueError("O intervalo precisa ficar dentro da jornada.")
    return {
        "dia_semana": int(dia.get("dia_semana")),
        "ativo": ativo,
        "hora_entrada": entrada,
        "hora_saida": saida,
        "intervalo_inicio": intervalo_inicio,
        "intervalo_fim": intervalo_fim,
    }


def _jornada_resposta(profissional):
    gravados = {item.dia_semana: item for item in profissional.horarios.all()}
    dias = []
    for dia in range(7):
        item = gravados.get(dia)
        dias.append({
            "dia_semana": dia,
            "ativo": bool(item and item.ativo),
            "hora_entrada": (item.hora_entrada if item else time(9, 0)).strftime("%H:%M"),
            "hora_saida": (item.hora_saida if item else time(19, 0)).strftime("%H:%M"),
            "intervalo_inicio": item.intervalo_inicio.strftime("%H:%M") if item and item.intervalo_inicio else "",
            "intervalo_fim": item.intervalo_fim.strftime("%H:%M") if item and item.intervalo_fim else "",
        })
    return dias


class JornadaProfissionalView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Profissional
    not_found_message = "Profissional não encontrado."

    def get(self, request, pk):
        profissional, erro = self.object_or_404(pk)
        if erro:
            return erro
        return Response(_jornada_resposta(profissional))

    def put(self, request, pk):
        profissional, erro = self.object_or_404(pk)
        if erro:
            return erro
        bruto = request.data if isinstance(request.data, list) else request.data.get("dias")
        if not isinstance(bruto, list) or len(bruto) != 7:
            return _erro("Informe os sete dias da jornada.")
        try:
            dias = [_validar_dia_jornada(item) for item in bruto]
        except (TypeError, ValueError) as exc:
            return _erro(str(exc))
        if {item["dia_semana"] for item in dias} != set(range(7)):
            return _erro("Informe cada dia da semana uma vez.")
        for item in dias:
            HorarioTrabalho.objects.update_or_create(
                profissional=profissional,
                dia_semana=item["dia_semana"],
                defaults=item,
            )
        return Response(_jornada_resposta(profissional))


class BloqueioListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        qs = Bloqueio.objects.filter(is_active=True).select_related("profissional")
        dados = [
            {
                "id": item.id,
                "titulo": item.titulo,
                "tipo": item.tipo,
                "data_inicio": item.data_inicio.isoformat(),
                "data_fim": item.data_fim.isoformat(),
                "horario_inicio": item.horario_inicio.isoformat() if item.horario_inicio else None,
                "horario_fim": item.horario_fim.isoformat() if item.horario_fim else None,
                "profissional": item.profissional_id,
                "profissional_nome": item.profissional.nome if item.profissional_id else "Salão",
            }
            for item in qs.order_by("data_inicio")[:200]
        ]
        return Response(dados)

    def post(self, request):
        titulo = (request.data.get("titulo") or "").strip()
        if len(titulo) < 2:
            return _erro("Informe o motivo do bloqueio.")
        try:
            data_inicio = datetime.strptime(str(request.data.get("data_inicio"))[:10], "%Y-%m-%d").date()
            data_fim = datetime.strptime(str(request.data.get("data_fim") or request.data.get("data_inicio"))[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return _erro("Informe a data do bloqueio.")
        profissional = None
        if request.data.get("profissional"):
            profissional = Profissional.objects.filter(pk=request.data.get("profissional"), is_active=True).first()
        try:
            horario_inicio = _hora(request.data.get("horario_inicio"))
            horario_fim = _hora(request.data.get("horario_fim"))
        except ValueError as exc:
            return _erro(str(exc))
        if bool(horario_inicio) != bool(horario_fim) or (horario_inicio and horario_inicio >= horario_fim):
            return _erro("Informe o começo e o fim do horário, com o fim depois do começo.")
        if data_fim < data_inicio:
            return _erro("A data final precisa ser igual ou posterior à inicial.")
        bloqueio = Bloqueio.objects.create(
            titulo=titulo,
            tipo=request.data.get("tipo") or "folga",
            data_inicio=data_inicio,
            data_fim=data_fim,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim,
            profissional=profissional,
        )
        return Response({"id": bloqueio.id}, status=status.HTTP_201_CREATED)


class BloqueioDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Bloqueio
    not_found_message = "Folga não encontrada."

    def delete(self, request, pk):
        bloqueio, erro = self.object_or_404(pk)
        if erro:
            return erro
        bloqueio.is_active = False
        bloqueio.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


def _dinheiro(valor) -> str:
    quantia = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    texto = f"{quantia:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _venda_ligada(recibo):
    """O comprovante antigo aponta da venda para o recebimento. O novo aponta nos dois sentidos."""
    if recibo.venda_id:
        return recibo.venda
    ligadas = list(recibo.vendas.all())
    return next((venda for venda in ligadas if venda.is_active), None) or (ligadas[0] if ligadas else None)


def _dados_do_comprovante(venda):
    if venda is None:
        return {"numero": None, "operador": ""}
    return {"numero": venda.numero, "operador": venda.operador_nome or ""}


class ResumoView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        agora = timezone.localtime()
        inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_dia = inicio_dia + timedelta(days=1)
        inicio_mes = inicio_dia.replace(day=1)
        if inicio_mes.month == 12:
            fim_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1)
        else:
            fim_mes = inicio_mes.replace(month=inicio_mes.month + 1)
        inicio_semana = inicio_dia - timedelta(days=inicio_dia.weekday())
        fim_semana = inicio_semana + timedelta(days=7)

        do_dia = list(
            Agendamento.objects.filter(inicio__gte=inicio_dia, inicio__lt=fim_dia)
            .exclude(status="CANCELLED")
            .select_related("cliente", "servico", "profissional")
            .order_by("inicio")
        )
        recebidos_mes = list(
            Recebimento.objects.filter(is_active=True, created_at__gte=inicio_mes, created_at__lt=fim_mes)
            .select_related("agendamento__servico", "profissional")
        )
        recebidos_dia = [
            item for item in recebidos_mes
            if inicio_dia <= timezone.localtime(item.created_at) < fim_dia
        ]
        receita = sum((item.valor for item in recebidos_mes), Decimal("0"))
        faturamento_dia = sum((item.valor for item in recebidos_dia), Decimal("0"))
        novos = Cliente.objects.filter(created_at__gte=inicio_mes, created_at__lt=fim_mes, is_active=True).count()
        ticket = (receita / len(recebidos_mes)) if recebidos_mes else Decimal("0")
        ativos = Cliente.objects.filter(is_active=True).count()
        minutos = sum(item.duracao_minutos for item in do_dia if item.status in STATUS_OCUPA_HORARIO)
        profissionais = max(Profissional.objects.filter(is_active=True).count(), 1)
        ocupacao = min(100, round(minutos / (profissionais * 10 * 60) * 100))

        por_servico = {}
        por_profissional = {}
        for item in recebidos_mes:
            chave = item.agendamento.servico.nome
            atual = por_servico.setdefault(chave, {"nome": chave, "quantidade": 0, "receita": Decimal("0")})
            atual["quantidade"] += 1
            atual["receita"] += item.valor
            comissao = por_profissional.setdefault(item.profissional_id, {
                "nome": item.profissional.nome,
                "quantidade": 0,
                "comissao": Decimal("0"),
            })
            comissao["quantidade"] += 1
            comissao["comissao"] += item.comissao_valor
        comissoes = sorted(por_profissional.values(), key=lambda item: item["comissao"], reverse=True)
        servicos = sorted(por_servico.values(), key=lambda item: item["receita"], reverse=True)[:5]

        semana = []
        for offset in range(7):
            dia = inicio_semana + timedelta(days=offset)
            total = Agendamento.objects.filter(
                inicio__gte=dia,
                inicio__lt=dia + timedelta(days=1),
            ).exclude(status__in=["CANCELLED", "NO_SHOW"]).count()
            semana.append({
                "data": dia.date().isoformat(),
                "rotulo": dia.strftime("%a"),
                "total": total,
            })

        aniversariantes = []
        for cliente in Cliente.objects.filter(is_active=True, data_nascimento__isnull=False):
            if cliente.data_nascimento.month == agora.month:
                aniversariantes.append({
                    "nome": cliente.nome,
                    "dia": cliente.data_nascimento.strftime("%d/%m"),
                })
        aniversariantes.sort(key=lambda item: item["dia"])

        serie_mes = []
        for deslocamento in range((fim_mes - inicio_mes).days):
            dia = inicio_mes + timedelta(days=deslocamento)
            itens_dia = [
                item for item in recebidos_mes
                if timezone.localtime(item.created_at).date() == dia.date()
            ]
            valor_dia = sum((item.valor for item in itens_dia), Decimal("0"))
            serie_mes.append({"dia": dia.day, "valor": float(valor_dia)})

        loja, prof = contexto_salao(request)
        config = _config()
        return Response({
            "painel": config.painel,
            "pode_trocar": usuario_e_admin(loja, prof, request.user),
            "hoje": {
                "agendamentos": len([item for item in do_dia if item.status != "NO_SHOW"]),
                "em_andamento": len([item for item in do_dia if item.status == "IN_PROGRESS"]),
                "concluidos": len([item for item in do_dia if item.status == "COMPLETED"]),
                "faturamento": _dinheiro(faturamento_dia),
                "ocupacao": ocupacao,
            },
            "mes": {
                "receita": _dinheiro(receita),
                "novos_clientes": novos,
                "ticket": _dinheiro(ticket),
                "clientes_ativos": ativos,
            },
            "semana": semana,
            "serie_mes": serie_mes,
            "servicos": [
                {**item, "receita": _dinheiro(item["receita"])}
                for item in servicos
            ],
            "comissoes": [
                {**item, "comissao": _dinheiro(item["comissao"])}
                for item in comissoes
            ],
            "aniversariantes": aniversariantes[:8],
            "agenda_hoje": [
                {
                    "id": item.id,
                    "hora": timezone.localtime(item.inicio).strftime("%H:%M"),
                    "cliente": item.cliente.nome,
                    "servico": item.servico.nome,
                    "profissional": item.profissional.nome,
                    "status": item.status,
                    "status_label": item.get_status_display(),
                }
                for item in do_dia
            ],
        })


def _agendamento_completo(pk):
    return (
        Agendamento.objects.select_related("cliente", "profissional", "servico")
        .prefetch_related("recebimentos")
        .filter(pk=pk)
        .first()
    )


class ReceberAgendamentoView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def post(self, request, pk):
        agendamento = _agendamento_completo(pk)
        if agendamento is None:
            return _erro("Agendamento não encontrado.", status.HTTP_404_NOT_FOUND)
        if agendamento.status != "COMPLETED":
            return _erro("Conclua o atendimento antes de receber.")
        if any(item.is_active for item in agendamento.recebimentos.all()):
            return _erro("Este atendimento já foi recebido.")
        config = _config()
        origem = (request.data.get("origem") or "agenda").strip()
        if origem not in {"agenda", "caixa"}:
            origem = "agenda"
        loja, prof = contexto_salao(request)
        motivo = motivo_bloqueio_recebimento(
            config.local_recebimento,
            origem,
            papel_salao(loja, prof, request.user, config.modelo),
        )
        if motivo:
            return _erro(motivo, status.HTTP_403_FORBIDDEN)
        try:
            desconto = quantia(request.data.get("desconto") or 0)
            valor, comissao, percentual = comissao_do_atendimento(
                agendamento.profissional,
                agendamento.servico_id,
                agendamento.servico.preco,
                desconto,
            )
            partes = interpretar_formas(request.data, valor)
        except ValueError as exc:
            return _erro(str(exc))
        Recebimento.objects.create(
            agendamento=agendamento,
            profissional=agendamento.profissional,
            valor_servico=agendamento.servico.preco,
            desconto=desconto,
            valor=valor,
            forma=partes[0]["forma"] if partes else "dinheiro",
            partes=partes,
            comissao_percentual=percentual,
            comissao_valor=comissao,
            observacao=(request.data.get("observacao") or "")[:200],
        )
        return Response(AgendamentoSerializer(_agendamento_completo(pk)).data, status=status.HTTP_201_CREATED)


class RecebimentoDetailView(GetObjectMixin, APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]
    model_class = Recebimento
    not_found_message = "Recebimento não encontrado."

    def delete(self, request, pk):
        recebimento, erro = self.object_or_404(pk)
        if erro:
            return erro
        if not recebimento.is_active:
            return _erro(self.not_found_message, status.HTTP_404_NOT_FOUND)
        from .estoque_service import estornar_operacao

        estornar_operacao(recebimento)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaixaView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        inicio_txt = request.query_params.get("start")
        fim_txt = request.query_params.get("end")
        if inicio_txt and fim_txt:
            try:
                inicio = interpretar_inicio(inicio_txt)
                fim = interpretar_inicio(fim_txt)
            except ValueError as exc:
                return _erro(str(exc))
        else:
            agora = timezone.localtime()
            inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
            fim = inicio + timedelta(days=1)
        itens = list(
            Recebimento.objects.filter(is_active=True, created_at__gte=inicio, created_at__lt=fim)
            .select_related("agendamento__cliente", "agendamento__servico", "profissional", "venda")
            .prefetch_related("vendas")
            .order_by("-created_at")[:300]
        )
        total = Decimal("0")
        por_forma = {}
        por_profissional = {}
        for item in itens:
            total += item.valor
            for parte in item.partes or [{"forma": item.forma, "valor": item.valor}]:
                codigo = parte["forma"]
                forma = por_forma.setdefault(codigo, {"forma": codigo, "nome": dict(FORMAS_PAGAMENTO).get(codigo, codigo), "total": Decimal("0")})
                forma["total"] += Decimal(str(parte["valor"]))
            comissao = por_profissional.setdefault(item.profissional_id, {
                "nome": item.profissional.nome,
                "quantidade": 0,
                "recebido": Decimal("0"),
                "comissao": Decimal("0"),
            })
            comissao["quantidade"] += 1
            comissao["recebido"] += item.valor
            comissao["comissao"] += item.comissao_valor
        vendas = list(
            Venda.objects.filter(is_active=True, created_at__gte=inicio, created_at__lt=fim, valor_produtos__gt=0)
            .select_related("recebimento__profissional")
            .prefetch_related("itens")
            .order_by("-created_at")[:300]
        )
        for venda in vendas:
            total += venda.valor_produtos
            if venda.recebimento_id:
                profissional = venda.recebimento.profissional
                comissao = por_profissional.setdefault(profissional.id, {
                    "nome": profissional.nome,
                    "quantidade": 0,
                    "recebido": Decimal("0"),
                    "comissao": Decimal("0"),
                })
                comissao["comissao"] += sum((item.comissao_valor for item in venda.itens.all()), Decimal("0"))
            for parte in venda.partes_produtos or []:
                codigo = parte["forma"]
                forma = por_forma.setdefault(codigo, {"forma": codigo, "nome": dict(FORMAS_PAGAMENTO).get(codigo, codigo), "total": Decimal("0")})
                forma["total"] += Decimal(str(parte["valor"]))
        return Response({
            "total": _dinheiro(total),
            "quantidade": len(itens) + sum(1 for venda in vendas if venda.recebimento_id is None),
            "por_forma": [{**item, "total": _dinheiro(item["total"])} for item in por_forma.values()],
            "comissoes": [
                {**item, "recebido": _dinheiro(item["recebido"]), "comissao": _dinheiro(item["comissao"])}
                for item in sorted(por_profissional.values(), key=lambda atual: atual["comissao"], reverse=True)
            ],
            "recebimentos": [
                {
                    "id": item.id,
                    "quando": timezone.localtime(item.created_at).strftime("%d/%m %H:%M"),
                    "cliente": item.agendamento.cliente.nome,
                    "servico": item.agendamento.servico.nome,
                    "profissional": item.profissional.nome,
                    "forma": item.forma,
                    "forma_label": rotulo_formas(item.partes, item.forma),
                    "desconto": _dinheiro(item.desconto),
                    "valor": _dinheiro(item.valor),
                    "comissao": _dinheiro(item.comissao_valor),
                    "agendamento": item.agendamento_id,
                    **_dados_do_comprovante(_venda_ligada(item)),
                    "estornado": False,
                }
                for item in itens
            ] + [
                {
                    "id": venda.id,
                    "quando": timezone.localtime(venda.created_at).strftime("%d/%m %H:%M"),
                    "cliente": venda.cliente_nome or "Consumidor",
                    "servico": ", ".join(f"{item.quantidade} {item.nome}" for item in venda.itens.all()) or "Produto",
                    "profissional": "",
                    "forma": venda.forma,
                    "forma_label": rotulo_formas(venda.partes_produtos, venda.forma),
                    "desconto": "R$ 0,00",
                    "valor": _dinheiro(venda.valor_produtos),
                    "comissao": "R$ 0,00",
                    "agendamento": venda.agendamento_id,
                    "numero": venda.numero,
                    "operador": venda.operador_nome,
                    "estornado": False,
                }
                for venda in vendas
            ],
            "estornos": _estornos_do_caixa(inicio, fim),
        })


def _estornos_do_caixa(inicio, fim):
    from .models import Venda

    recibos = (
        Recebimento.objects.filter(is_active=False, created_at__gte=inicio, created_at__lt=fim)
        .select_related("agendamento__cliente", "agendamento__servico", "profissional", "venda")
        .prefetch_related("vendas")
        .order_by("-created_at")[:200]
    )
    vendas = (
        Venda.objects.filter(is_active=False, created_at__gte=inicio, created_at__lt=fim, recebimento__isnull=True)
        .order_by("-created_at")[:200]
    )
    return [
        {
            "id": item.id,
            "quando": timezone.localtime(item.created_at).strftime("%d/%m %H:%M"),
            "cliente": item.agendamento.cliente.nome,
            "servico": item.agendamento.servico.nome,
            "valor": _dinheiro(item.valor),
            "forma_label": rotulo_formas(item.partes, item.forma),
            **_dados_do_comprovante(_venda_ligada(item)),
        }
        for item in recibos
    ] + [
        {
            "id": venda.id,
            "quando": timezone.localtime(venda.created_at).strftime("%d/%m %H:%M"),
            "cliente": venda.cliente_nome or "Consumidor",
            "servico": "Produto",
            "valor": _dinheiro(venda.valor_produtos),
            "forma_label": rotulo_formas(venda.partes, venda.forma),
            "operador": venda.operador_nome,
            "numero": venda.numero,
        }
        for venda in vendas
    ]


class ComunicacaoView(APIView):
    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAuthenticated(), IsSalaoAdmin()]
        return [IsAuthenticated(), IsSalaoMembro()]

    def get(self, request):
        loja, prof = contexto_salao(request)
        dados = regras_de(_config())
        dados["whatsapp_pronto"] = whatsapp_pronto(getattr(loja, "id", None))
        dados["pode_gravar"] = usuario_e_admin(loja, prof, request.user) if loja else False
        return Response(dados)

    def put(self, request):
        try:
            campos = validar_regras(request.data)
        except (TypeError, ValueError) as exc:
            return _erro(str(exc) or "Não foi possível gravar as mensagens.")
        config = _config()
        for chave, valor in campos.items():
            setattr(config, chave, valor)
        config.save(update_fields=list(campos))
        return self.get(request)


class WhatsappAgendamentoView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def post(self, request, pk):
        agendamento = _agendamento_completo(pk)
        if agendamento is None:
            return _erro("Agendamento não encontrado.", status.HTTP_404_NOT_FOUND)
        evento = (request.data.get("evento") or "confirmacao").strip()
        ok, erro = enviar_evento(agendamento, evento, user=request.user, manual=True)
        if not ok:
            return _erro(erro or "Não foi possível enviar o WhatsApp.")
        return Response({"enviado": True})
