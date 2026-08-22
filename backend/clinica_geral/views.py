from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context, get_current_loja_id

from .models import (
    ConfiguracaoConsultorio,
    Consulta,
    Evolucao,
    FechamentoCaixa,
    GuiaTiss,
    LoteTiss,
    Paciente,
    Prescricao,
    Tarefa,
)
from .serializers import (
    ConfiguracaoConsultorioSerializer,
    ConsultaSerializer,
    EvolucaoSerializer,
    FechamentoCaixaSerializer,
    GuiaTissSerializer,
    LoteTissSerializer,
    PacienteListaSerializer,
    PacienteSerializer,
    PrescricaoSerializer,
    TarefaSerializer,
)


class PacienteViewSet(BaseModelViewSet):
    serializer_class = PacienteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return PacienteListaSerializer
        return PacienteSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Paciente.objects.filter(is_active=True)
        letra = (self.request.query_params.get("letra") or "").strip().upper()
        busca = (self.request.query_params.get("q") or "").strip()
        if letra and letra != "TODOS" and len(letra) == 1:
            qs = qs.filter(nome__istartswith=letra)
        if busca:
            qs = qs.filter(Q(nome__icontains=busca) | Q(nome_social__icontains=busca) | Q(cpf__icontains=busca))
        return qs.distinct()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class ConsultaViewSet(BaseModelViewSet):
    serializer_class = ConsultaSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Consulta.objects.filter(is_active=True).select_related("paciente")
        data = (self.request.query_params.get("data") or "").strip()
        de = (self.request.query_params.get("de") or "").strip()
        ate = (self.request.query_params.get("ate") or "").strip()
        if data:
            qs = qs.filter(data=data)
        if de:
            qs = qs.filter(data__gte=de)
        if ate:
            qs = qs.filter(data__lte=ate)
        return qs

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        user = self.request.user
        nome = (getattr(user, "get_full_name", lambda: "")() or getattr(user, "username", "") or "").strip()
        consulta = serializer.save(agendado_por=nome)
        try:
            from whatsapp.confirmacao_agenda_service import disparar_confirmacao_se_hoje

            from .whatsapp_agenda import ConsultaWhatsAppAdapter

            disparar_confirmacao_se_hoje(ConsultaWhatsAppAdapter(consulta))
        except Exception:
            pass

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.status = "desmarcado"
        instance.save(update_fields=["is_active", "status", "updated_at"])

    @action(detail=True, methods=["post"])
    def recepcionar(self, request, pk=None):
        """Atualiza ficha do paciente e marca a consulta como recepcionada."""
        ensure_loja_context(request)
        consulta = self.get_object()
        paciente = consulta.paciente
        campos = (
            "numero_prontuario",
            "nome",
            "nome_social",
            "cpf",
            "rg",
            "rne",
            "passaporte",
            "pais_emissor",
            "nome_mae",
            "telefone_fixo",
            "telefone",
            "email",
            "quem_indicou",
            "alergias",
        )
        for campo in campos:
            if campo in request.data:
                setattr(paciente, campo, request.data.get(campo) or "")
        paciente.save()
        if "convenio" in request.data:
            consulta.convenio = request.data.get("convenio") or consulta.convenio
        consulta.status = "recepcionado"
        consulta.save(update_fields=["convenio", "status", "updated_at"])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk=None):
        ensure_loja_context(request)
        consulta = self.get_object()
        consulta.status = "checkin"
        consulta.save(update_fields=["status", "updated_at"])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=["post"], url_path="abrir-tele")
    def abrir_tele(self, request, pk=None):
        ensure_loja_context(request)
        consulta = self.get_object()
        config = _config_consultorio()
        usados = (
            Consulta.objects.filter(data__month=consulta.data.month, data__year=consulta.data.year)
            .aggregate(t=Sum("tele_minutos"))
            .get("t")
            or 0
        )
        teto = config.teto_tele_minutos or 600
        if usados >= teto:
            return Response({"detail": "Cota de telemedicina do mês esgotada (10h)."}, status=400)
        if not consulta.tele_sala_url:
            consulta.tele_sala_url = f"https://meet.jit.si/lwk-cg-{consulta.loja_id}-{consulta.id}"
            consulta.save(update_fields=["tele_sala_url", "updated_at"])
        return Response(
            {
                **ConsultaSerializer(consulta).data,
                "tele_minutos_mes": int(usados),
                "teto_tele_minutos": teto,
            }
        )

    @action(detail=True, methods=["post"], url_path="registrar-tele")
    def registrar_tele(self, request, pk=None):
        ensure_loja_context(request)
        consulta = self.get_object()
        try:
            extra = max(0, int(request.data.get("minutos") or 0))
        except (TypeError, ValueError):
            extra = 0
        consulta.tele_minutos = (consulta.tele_minutos or 0) + extra
        consulta.save(update_fields=["tele_minutos", "updated_at"])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=False, methods=["get"], url_path="horarios-livres")
    def horarios_livres(self, request):
        """Slots conforme a configuração do consultório, sem consulta no dia (e no seguinte)."""
        ensure_loja_context(request)
        raw = (request.query_params.get("data") or "").strip()
        try:
            dia = datetime.strptime(raw, "%Y-%m-%d").date() if raw else datetime.now().date()
        except ValueError:
            dia = datetime.now().date()
        inicio, fim_hora, passo = _agenda_janela()

        def slots_do_dia(d):
            ocupados = {
                c.hora.strftime("%H:%M")
                for c in Consulta.objects.filter(is_active=True, data=d).exclude(status="desmarcado")
            }
            livres = []
            cursor = datetime.combine(d, inicio)
            fim = datetime.combine(d, fim_hora)
            while cursor < fim:
                hhmm = cursor.strftime("%H:%M")
                if hhmm not in ocupados:
                    livres.append(hhmm)
                cursor += timedelta(minutes=passo)
            return livres

        return Response(
            {
                "dias": [
                    {"data": dia.isoformat(), "horarios": slots_do_dia(dia)},
                    {
                        "data": (dia + timedelta(days=1)).isoformat(),
                        "horarios": slots_do_dia(dia + timedelta(days=1)),
                    },
                ]
            }
        )


class TarefaViewSet(BaseModelViewSet):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Tarefa.objects.all()
        data = (self.request.query_params.get("data") or "").strip()
        if data:
            qs = qs.filter(data=data)
        return qs


class ConfiguracaoConsultorioViewSet(BaseModelViewSet):
    serializer_class = ConfiguracaoConsultorioSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        ensure_loja_context(self.request)
        return ConfiguracaoConsultorio.objects.all()

    @action(detail=False, methods=["get", "put", "patch"], url_path="atual")
    def atual(self, request):
        ensure_loja_context(request)
        config = _config_consultorio()
        if request.method == "GET":
            return Response(ConfiguracaoConsultorioSerializer(config).data)
        serializer = ConfiguracaoConsultorioSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MeView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request):
        ensure_loja_context(request)
        user = request.user
        nome = (user.get_full_name() or user.first_name or user.username or "").strip()
        return Response(
            {
                "username": user.username,
                "nome": nome,
                "email": user.email or "",
            }
        )


def _config_consultorio():
    loja_id = get_current_loja_id()
    config = ConfiguracaoConsultorio.objects.first()
    if config:
        return config
    defaults = {"hora_inicio": time(8, 0), "hora_fim": time(18, 0), "duracao_minutos": 15}
    if loja_id:
        defaults["loja_id"] = loja_id
    return ConfiguracaoConsultorio.objects.create(**defaults)


def _agenda_janela():
    config = ConfiguracaoConsultorio.objects.first()
    if not config:
        return time(8, 0), time(18, 0), 15
    passo = config.duracao_minutos or 15
    return config.hora_inicio, config.hora_fim, passo


def _periodo(request):
    hoje = datetime.now().date()
    raw_de = (request.query_params.get("de") or "").strip()
    raw_ate = (request.query_params.get("ate") or "").strip()
    try:
        de = datetime.strptime(raw_de, "%Y-%m-%d").date() if raw_de else hoje.replace(day=1)
    except ValueError:
        de = hoje.replace(day=1)
    try:
        ate = datetime.strptime(raw_ate, "%Y-%m-%d").date() if raw_ate else hoje
    except ValueError:
        ate = hoje
    return de, ate


class RelatoriosView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request):
        ensure_loja_context(request)
        tipo = (request.query_params.get("tipo") or "atendimentos").strip()
        de, ate = _periodo(request)
        consultas = Consulta.objects.filter(data__gte=de, data__lte=ate)
        pacientes = Paciente.objects.filter(is_active=True)

        if tipo == "indicacao":
            grupos = (
                pacientes.exclude(quem_indicou="")
                .values("quem_indicou")
                .annotate(total=Count("id"))
                .order_by("-total")
            )
            return Response(
                {
                    "de": de.isoformat(),
                    "ate": ate.isoformat(),
                    "sem_indicacao": pacientes.filter(Q(quem_indicou="") | Q(quem_indicou__isnull=True)).count(),
                    "itens": [{"indicacao": g["quem_indicou"], "total": g["total"]} for g in grupos],
                }
            )

        if tipo == "status":
            grupos = consultas.values("status").annotate(total=Count("id")).order_by("-total")
            return Response(
                {
                    "de": de.isoformat(),
                    "ate": ate.isoformat(),
                    "total": consultas.count(),
                    "itens": [{"status": g["status"], "total": g["total"]} for g in grupos],
                }
            )

        if tipo == "financeiro":
            base = consultas.exclude(status__in=("desmarcado", "faltou"))
            grupos = base.values("convenio").annotate(total=Count("id"), valor=Sum("valor")).order_by("-total")
            soma = base.aggregate(v=Sum("valor")).get("v") or Decimal("0")
            return Response(
                {
                    "de": de.isoformat(),
                    "ate": ate.isoformat(),
                    "total": base.count(),
                    "valor_total": str(soma),
                    "itens": [
                        {
                            "convenio": g["convenio"] or "PARTICULAR",
                            "total": g["total"],
                            "valor": str(g["valor"] or 0),
                        }
                        for g in grupos
                    ],
                }
            )

        if tipo == "outros":
            return Response(
                {
                    "de": de.isoformat(),
                    "ate": ate.isoformat(),
                    "faltas": consultas.filter(status="faltou").count(),
                    "desmarcados": consultas.filter(status="desmarcado").count(),
                    "primeiras": consultas.filter(tipo="primeira").count(),
                    "retornos": consultas.filter(tipo="retorno").count(),
                    "pacientes_novos": pacientes.filter(
                        created_at__date__gte=de, created_at__date__lte=ate
                    ).count(),
                    "pacientes_ativos": pacientes.count(),
                }
            )

        itens = (
            consultas.exclude(status="desmarcado")
            .select_related("paciente")
            .order_by("data", "hora")[:300]
        )
        return Response(
            {
                "de": de.isoformat(),
                "ate": ate.isoformat(),
                "total": consultas.exclude(status="desmarcado").count(),
                "itens": ConsultaSerializer(itens, many=True).data,
            }
        )


class EvolucaoViewSet(BaseModelViewSet):
    serializer_class = EvolucaoSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Evolucao.objects.select_related("consulta", "paciente")
        paciente = (self.request.query_params.get("paciente") or "").strip()
        consulta = (self.request.query_params.get("consulta") or "").strip()
        if paciente:
            qs = qs.filter(paciente_id=paciente)
        if consulta:
            qs = qs.filter(consulta_id=consulta)
        return qs

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        config = _config_consultorio()
        serializer.save(especialidade=serializer.validated_data.get("especialidade") or config.especialidade)


class PrescricaoViewSet(BaseModelViewSet):
    serializer_class = PrescricaoSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Prescricao.objects.prefetch_related("itens").select_related("paciente", "consulta")
        consulta = (self.request.query_params.get("consulta") or "").strip()
        if consulta:
            qs = qs.filter(consulta_id=consulta)
        return qs

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        ensure_loja_context(request)
        from .pdf_service import pdf_receita

        presc = self.get_object()
        data = pdf_receita(presc, presc.consulta, presc.paciente, _config_consultorio())
        resp = HttpResponse(data, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="receita-{presc.id}.pdf"'
        return resp


class LoteTissViewSet(BaseModelViewSet):
    serializer_class = LoteTissSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        return LoteTiss.objects.annotate(guias_count=Count("guias"))

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        lote = serializer.save()
        if not lote.numero:
            lote.numero = str(lote.id).zfill(6)
            lote.save(update_fields=["numero"])


class GuiaTissViewSet(BaseModelViewSet):
    serializer_class = GuiaTissSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = GuiaTiss.objects.select_related("consulta__paciente", "lote")
        lote = (self.request.query_params.get("lote") or "").strip()
        if lote:
            qs = qs.filter(lote_id=lote)
        return qs

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        consulta = serializer.validated_data["consulta"]
        guia = serializer.save(valor=serializer.validated_data.get("valor") or consulta.valor)
        if not guia.numero_guia:
            guia.numero_guia = f"G{guia.id:06d}"
            guia.save(update_fields=["numero_guia"])

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        ensure_loja_context(request)
        from .pdf_service import pdf_guia_tiss

        guia = self.get_object()
        data = pdf_guia_tiss(guia, guia.consulta, guia.consulta.paciente, _config_consultorio())
        resp = HttpResponse(data, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="guia-tiss-{guia.numero_guia or guia.id}.pdf"'
        return resp


class FechamentoCaixaViewSet(BaseModelViewSet):
    serializer_class = FechamentoCaixaSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = FechamentoCaixa.objects.all()
        data = (self.request.query_params.get("data") or "").strip()
        if data:
            qs = qs.filter(data=data)
        return qs

    @action(detail=False, methods=["get", "post"], url_path="dia")
    def dia(self, request):
        ensure_loja_context(request)
        raw = (request.query_params.get("data") or request.data.get("data") or "").strip()
        try:
            dia = datetime.strptime(raw, "%Y-%m-%d").date() if raw else datetime.now().date()
        except ValueError:
            dia = datetime.now().date()
        qs = Consulta.objects.filter(data=dia).exclude(status__in=("desmarcado", "faltou"))
        particular = qs.filter(Q(convenio="") | Q(convenio__iexact="PARTICULAR")).aggregate(v=Sum("valor")).get("v") or 0
        convenio = qs.exclude(Q(convenio="") | Q(convenio__iexact="PARTICULAR")).aggregate(v=Sum("valor")).get("v") or 0
        if request.method == "POST":
            fech, _ = FechamentoCaixa.objects.update_or_create(
                data=dia,
                defaults={
                    "total_particular": particular,
                    "total_convenio": convenio,
                    "observacoes": request.data.get("observacoes") or "",
                },
            )
            return Response(FechamentoCaixaSerializer(fech).data)
        return Response(
            {
                "data": dia.isoformat(),
                "total_particular": str(particular),
                "total_convenio": str(convenio),
                "consultas": qs.count(),
            }
        )


class ProntuarioPacienteView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request, paciente_id):
        ensure_loja_context(request)
        paciente = Paciente.objects.filter(pk=paciente_id, is_active=True).first()
        if not paciente:
            return Response({"detail": "Paciente não encontrado."}, status=404)
        evolucoes = Evolucao.objects.filter(paciente=paciente).select_related("consulta")
        prescricoes = Prescricao.objects.filter(paciente=paciente).prefetch_related("itens")
        return Response(
            {
                "paciente": PacienteSerializer(paciente).data,
                "evolucoes": EvolucaoSerializer(evolucoes, many=True).data,
                "prescricoes": PrescricaoSerializer(prescricoes, many=True).data,
            }
        )


class EvolucaoPDFView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request, pk):
        ensure_loja_context(request)
        from .pdf_service import pdf_evolucao

        ev = Evolucao.objects.select_related("consulta", "paciente").filter(pk=pk).first()
        if not ev:
            return Response({"detail": "Evolução não encontrada."}, status=404)
        data = pdf_evolucao(ev, ev.consulta, ev.paciente, _config_consultorio())
        resp = HttpResponse(data, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="evolucao-{ev.id}.pdf"'
        return resp
