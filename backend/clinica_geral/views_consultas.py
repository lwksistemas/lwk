from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .agenda_service import (
    aplicar_checkin,
    aplicar_recepcao,
    cancelar_consulta,
    disparar_confirmacao_consulta,
    horarios_livres_janela,
    nome_usuario,
    parse_iso_date,
)
from .config_service import get_or_create_config
from .models import Consulta
from .serializers import ConsultaSerializer
from .tele_service import CotaTeleEsgotada, abrir_sala, registrar_minutos


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
        consulta = serializer.save(agendado_por=nome_usuario(self.request.user))
        disparar_confirmacao_consulta(consulta)

    def perform_destroy(self, instance):
        cancelar_consulta(instance)

    @action(detail=True, methods=["post"])
    def recepcionar(self, request, pk=None):
        ensure_loja_context(request)
        consulta = aplicar_recepcao(self.get_object(), request.data)
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk=None):
        ensure_loja_context(request)
        consulta = aplicar_checkin(self.get_object())
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=["post"], url_path="abrir-tele")
    def abrir_tele(self, request, pk=None):
        ensure_loja_context(request)
        consulta = self.get_object()
        try:
            consulta, usados, teto = abrir_sala(consulta, get_or_create_config().teto_tele_minutos)
        except CotaTeleEsgotada as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {
                **ConsultaSerializer(consulta).data,
                "tele_minutos_mes": usados,
                "teto_tele_minutos": teto,
            }
        )

    @action(detail=True, methods=["post"], url_path="registrar-tele")
    def registrar_tele(self, request, pk=None):
        ensure_loja_context(request)
        consulta = registrar_minutos(self.get_object(), request.data.get("minutos"))
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=False, methods=["get"], url_path="horarios-livres")
    def horarios_livres(self, request):
        ensure_loja_context(request)
        dia = parse_iso_date(request.query_params.get("data") or "")
        return Response({"dias": horarios_livres_janela(dia)})
