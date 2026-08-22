from datetime import datetime, time, timedelta

from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .models import Consulta, Paciente, Tarefa
from .serializers import (
    ConsultaSerializer,
    PacienteListaSerializer,
    PacienteSerializer,
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
        serializer.save(agendado_por=nome)

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

    @action(detail=False, methods=["get"], url_path="horarios-livres")
    def horarios_livres(self, request):
        """Slots de 15 min (08:00–18:00) sem consulta no dia informado (e no seguinte)."""
        ensure_loja_context(request)
        raw = (request.query_params.get("data") or "").strip()
        try:
            dia = datetime.strptime(raw, "%Y-%m-%d").date() if raw else datetime.now().date()
        except ValueError:
            dia = datetime.now().date()

        def slots_do_dia(d):
            ocupados = {
                c.hora.strftime("%H:%M")
                for c in Consulta.objects.filter(is_active=True, data=d).exclude(status="desmarcado")
            }
            livres = []
            cursor = datetime.combine(d, time(8, 0))
            fim = datetime.combine(d, time(18, 0))
            while cursor < fim:
                hhmm = cursor.strftime("%H:%M")
                if hhmm not in ocupados:
                    livres.append(hhmm)
                cursor += timedelta(minutes=15)
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
            grupos = (
                consultas.exclude(status="desmarcado")
                .values("convenio")
                .annotate(total=Count("id"))
                .order_by("-total")
            )
            return Response(
                {
                    "de": de.isoformat(),
                    "ate": ate.isoformat(),
                    "total": consultas.exclude(status="desmarcado").count(),
                    "itens": [{"convenio": g["convenio"] or "PARTICULAR", "total": g["total"]} for g in grupos],
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
