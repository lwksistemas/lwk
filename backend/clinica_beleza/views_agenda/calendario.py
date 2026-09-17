"""GET do calendário FullCalendar."""
import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.permissions import CLINICA_AGENDA, resolve_agenda_professional_scope
from clinica_beleza.serializers import AgendaEventSerializer
from clinica_beleza.views_agenda.helpers import (
    _agenda_events_queryset,
    _apply_agenda_appointment_scope,
)

logger = logging.getLogger(__name__)


class AgendaView(APIView):
    """GET /clinica-beleza/agenda/"""

    permission_classes = CLINICA_AGENDA

    def get(self, request):
        qs = (
            _agenda_events_queryset()
            .filter(
                patient__is_active=True,
            )
            .filter(
                Q(professional__isnull=True) | Q(professional__is_active=True),
            )
        )
        qs = _apply_agenda_appointment_scope(qs, request)
        start_raw = request.query_params.get("start")
        end_raw = request.query_params.get("end")
        if start_raw:
            qs = qs.filter(date__gte=start_raw)
        if end_raw:
            qs = qs.filter(date__lte=end_raw)

        # Evita payload enorme: janela máx. ~3 meses; sem params → ~2 meses em torno de agora
        max_span_days = 93

        def _bound_date(raw: str):
            dt = parse_datetime(raw)
            if dt is not None:
                return timezone.localtime(dt).date() if timezone.is_aware(dt) else dt.date()
            return parse_date(raw[:10] if len(raw) >= 10 else raw)

        if start_raw and end_raw:
            start_d = _bound_date(start_raw)
            end_d = _bound_date(end_raw)
            if start_d and end_d and (end_d - start_d).days > max_span_days:
                return Response(
                    {"error": f"Intervalo máximo da agenda: {max_span_days} dias."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif not start_raw and not end_raw:
            agora = timezone.now()
            qs = qs.filter(date__gte=agora - timedelta(days=7), date__lte=agora + timedelta(days=60))
        scope = resolve_agenda_professional_scope(request)
        if scope is None and (p := request.query_params.get("professional")):
            qs = qs.filter(professional_id=p)
        appointments = list(qs.order_by("date"))
        logger.info("GET agenda n=%s", len(appointments))
        from clinica_beleza.retorno_service import verificar_retorno_appointments_batch

        retorno_map = verificar_retorno_appointments_batch(appointments)
        return Response(
            AgendaEventSerializer(
                appointments,
                many=True,
                context={"request": request, "retorno_by_appointment_id": retorno_map},
            ).data,
        )
