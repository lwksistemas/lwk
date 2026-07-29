"""Views de Dashboard e Info da Loja — Clínica da Beleza
"""
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.middleware import get_current_loja_id

from .dashboard_service import (
    build_dashboard_data,
    next_appointments_queryset,
    parse_dashboard_period,
)
from .loja_contato_api import patch_contato_loja
from .permissions import CLINICA_ADMIN, CLINICA_RECEPCAO
from .serializers import AppointmentListSerializer
from .utils import DASHBOARD_CACHE_VERSION, LojaContextHelper


class LojaInfoView(APIView):
    """GET /clinica-beleza/loja-info/ — dados da loja (recibo).
    PATCH — telefone/e-mail de contato exibidos no recibo (admin).
    """

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [perm() for perm in CLINICA_ADMIN]
        return [perm() for perm in CLINICA_RECEPCAO]

    def get(self, request):
        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response({"error": "Contexto de loja não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(info)

    def patch(self, request):
        return patch_contato_loja(request)


class DashboardView(APIView):
    """GET /clinica-beleza/dashboard/"""

    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {"error": "Contexto de loja não encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qp = request.query_params
        today = now().date()
        current = now()

        def _query_int(value):
            if not value:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        _, _, filter_mes, filter_ano = parse_dashboard_period(
            mes=_query_int(qp.get("mes")),
            ano=_query_int(qp.get("ano")),
            today=today,
        )

        period = (qp.get("period") or "proximos").strip().lower()
        professional_id = qp.get("professional")

        cache_key = (
            f'clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{filter_ano}_{filter_mes:02d}'
            f'_{period}_{professional_id or "all"}'
        )
        skip_cache = (qp.get("refresh") or "").strip().lower() in ("1", "true", "yes")
        if not skip_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

        payload = build_dashboard_data(
            mes=filter_mes,
            ano=filter_ano,
            period_raw=period,
            professional_raw=professional_id,
            today=today,
            current=current,
        )
        meta = payload.pop("_next_appointments_meta")
        payload["next_appointments"] = AppointmentListSerializer(
            next_appointments_queryset(
                period=meta["period"],
                professional_id=meta["professional_id"],
                today=meta["today"],
                current=meta["current"],
            )[: meta["limit"]],
            many=True,
        ).data

        cache.set(cache_key, payload, 120)
        return Response(payload)
