"""Helpers compartilhados das views de consulta."""
from rest_framework import status
from rest_framework.response import Response

from ..models import Consulta, Patient

_DEFAULT_SELECT = (
    "patient",
    "professional",
    "procedure",
    "protocol",
    "appointment",
    "appointment__nome_agenda",
    "local_atendimento",
    "convenio",
)
_DEFAULT_PREFETCH = (
    "appointment__appointment_procedures__procedure",
    "appointment__payment_set",
)


def get_consulta_or_404(pk, select_related=None, prefetch_related=None):
    """Busca consulta com select/prefetch padrão ou retorna (None, Response 404)."""
    if select_related is None:
        select_related = _DEFAULT_SELECT
    if prefetch_related is None:
        prefetch_related = _DEFAULT_PREFETCH
    try:
        consulta = (
            Consulta.objects.select_related(*select_related)
            .prefetch_related(*prefetch_related)
            .get(pk=pk)
        )
        return consulta, None
    except Consulta.DoesNotExist:
        return None, Response({"error": "Consulta não encontrada"}, status=status.HTTP_404_NOT_FOUND)


def get_patient_or_404(patient_id):
    """Busca paciente ou retorna (None, Response 404)."""
    try:
        return Patient.objects.get(pk=patient_id), None
    except Patient.DoesNotExist:
        return None, Response({"error": "Cliente não encontrado"}, status=status.HTTP_404_NOT_FOUND)
