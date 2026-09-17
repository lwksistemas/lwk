"""Escopo e queryset da agenda (profissional vs recepção)."""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from clinica_beleza.models import Appointment
from clinica_beleza.permissions import resolve_agenda_professional_scope


def _apply_agenda_appointment_scope(qs, request):
    """Profissional vê só agendamentos atribuídos a si; recepção/admin veem todos."""
    scope = resolve_agenda_professional_scope(request)
    if scope is None:
        return qs
    if not scope:
        return qs.none()
    return qs.filter(professional_id=scope)


def _apply_agenda_bloqueio_scope(qs, request):
    """Profissional: bloqueios próprios + globais (sem profissional)."""
    scope = resolve_agenda_professional_scope(request)
    if scope is None:
        return qs
    if not scope:
        return qs.filter(professional_id__isnull=True)
    return qs.filter(Q(professional_id=scope) | Q(professional_id__isnull=True))


def _agenda_scope_forbidden_response():
    return Response(
        {"error": "Sem permissão para acessar este agendamento."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _agenda_events_queryset():
    """Queryset otimizado para AgendaEventSerializer (evita N+1 em appointment_procedures)."""
    return (
        Appointment.objects
        .select_related(
            "patient", "professional", "procedure",
            "convenio", "nome_agenda", "local_atendimento", "consulta",
        )
        .prefetch_related("appointment_procedures__procedure")
    )
