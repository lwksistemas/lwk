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
from .catalogo import garantir_catalogo_inicial
from .models import PAINEIS, STATUS_AGENDAMENTO, STATUS_OCUPA_HORARIO, Agendamento, Bloqueio, Cliente, HorarioTrabalho, Profissional, SalaoConfig, Servico
from .permissions import IsSalaoAdmin, IsSalaoMembro, contexto_salao, usuario_e_admin
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


def _config():
    config = SalaoConfig.objects.first()
    if config is not None:
        return config
    return SalaoConfig.objects.create(painel="operacao")


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
        })

    def put(self, request):
        painel = (request.data.get("painel") or "").strip()
        if not painel_valido(painel):
            return _erro("Escolha Operação do dia, Gestão do mês ou Agenda da semana.")
        config = _config()
        config.painel = painel
        config.save(update_fields=["painel"])
        return Response({"painel": config.painel, "pode_trocar": True})


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
        qs = Profissional.objects.filter(is_active=True).order_by("nome")
        return Response(ProfissionalSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ProfissionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profissional = serializer.save()
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
        qs = Agendamento.objects.select_related("cliente", "profissional", "servico")
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
            return Agendamento.objects.select_related("cliente", "profissional", "servico").get(pk=pk)
        except Agendamento.DoesNotExist:
            return None

    def patch(self, request, pk):
        agendamento = self.get_object(pk)
        if agendamento is None:
            return _erro(self.not_found_message, status.HTTP_404_NOT_FOUND)
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
        return Response(AgendamentoSerializer(agendamento).data)

    def delete(self, request, pk):
        agendamento = self.get_object(pk)
        if agendamento is None:
            return _erro(self.not_found_message, status.HTTP_404_NOT_FOUND)
        agendamento.status = "CANCELLED"
        agendamento.save(update_fields=["status", "updated_at"])
        return Response(AgendamentoSerializer(agendamento).data)


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
        bloqueio = Bloqueio.objects.create(
            titulo=titulo,
            tipo=request.data.get("tipo") or "folga",
            data_inicio=data_inicio,
            data_fim=data_fim,
            profissional=profissional,
        )
        return Response({"id": bloqueio.id}, status=status.HTTP_201_CREATED)


def _dinheiro(valor) -> str:
    quantia = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    texto = f"{quantia:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


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
        do_mes = list(
            Agendamento.objects.filter(inicio__gte=inicio_mes, inicio__lt=fim_mes)
            .exclude(status__in=["CANCELLED", "NO_SHOW"])
            .select_related("servico", "cliente")
        )
        concluidos_mes = [item for item in do_mes if item.status == "COMPLETED"]
        receita = sum((item.servico.preco for item in concluidos_mes), Decimal("0"))
        novos = Cliente.objects.filter(created_at__gte=inicio_mes, created_at__lt=fim_mes, is_active=True).count()
        ticket = (receita / len(concluidos_mes)) if concluidos_mes else Decimal("0")
        ativos = Cliente.objects.filter(is_active=True).count()
        minutos = sum(item.duracao_minutos for item in do_dia if item.status in STATUS_OCUPA_HORARIO)
        profissionais = max(Profissional.objects.filter(is_active=True).count(), 1)
        ocupacao = min(100, round(minutos / (profissionais * 10 * 60) * 100))

        por_servico = {}
        for item in do_mes:
            chave = item.servico.nome
            atual = por_servico.setdefault(chave, {"nome": chave, "quantidade": 0, "receita": Decimal("0")})
            atual["quantidade"] += 1
            if item.status == "COMPLETED":
                atual["receita"] += item.servico.preco
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
                item for item in concluidos_mes
                if timezone.localtime(item.inicio).date() == dia.date()
            ]
            valor_dia = sum((item.servico.preco for item in itens_dia), Decimal("0"))
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
                "faturamento": _dinheiro(sum((item.servico.preco for item in do_dia if item.status == "COMPLETED"), Decimal("0"))),
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
