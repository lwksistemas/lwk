"""Helpers compartilhados das views de consulta."""
from rest_framework.response import Response
from rest_framework import status

from ..models import Consulta, Patient


def get_consulta_or_404(pk, select_related=None):
    """Busca consulta com select_related padrão ou retorna (None, Response 404)."""
    if select_related is None:
        select_related = (
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        )
    try:
        consulta = Consulta.objects.select_related(*select_related).get(pk=pk)
        return consulta, None
    except Consulta.DoesNotExist:
        return None, Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)


def get_patient_or_404(patient_id):
    """Busca paciente ou retorna (None, Response 404)."""
    try:
        return Patient.objects.get(pk=patient_id), None
    except Patient.DoesNotExist:
        return None, Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
