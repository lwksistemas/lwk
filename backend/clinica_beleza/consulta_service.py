"""
Sincronização de Consulta com mudanças de status do agendamento na agenda.
A consulta só é criada/atualizada quando o status muda na agenda — não manualmente na listagem.
"""
from django.utils.timezone import now

from .models import Appointment, Consulta


def _valor_consulta(appointment):
    try:
        return appointment.procedure.preco or 0
    except Exception:
        return 0


def sync_consulta_from_appointment_status(appointment, new_status, old_status=None):
    """
    Cria ou atualiza Consulta conforme o novo status do agendamento.
    Retorna a Consulta afetada ou None.
    """
    if new_status == old_status:
        return getattr(appointment, 'consulta', None)

    ts = now()

    if new_status == 'CONFIRMED':
        consulta, created = Consulta.objects.get_or_create(
            appointment=appointment,
            defaults={
                'patient_id': appointment.patient_id,
                'professional_id': appointment.professional_id,
                'procedure_id': appointment.procedure_id,
                'status': 'SCHEDULED',
                'valor_consulta': _valor_consulta(appointment),
                'loja_id': appointment.loja_id,
            },
        )
        if not created and consulta.status not in ('IN_PROGRESS', 'COMPLETED'):
            consulta.status = 'SCHEDULED'
            consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    if new_status == 'IN_PROGRESS':
        consulta, created = Consulta.objects.get_or_create(
            appointment=appointment,
            defaults={
                'patient_id': appointment.patient_id,
                'professional_id': appointment.professional_id,
                'procedure_id': appointment.procedure_id,
                'status': 'IN_PROGRESS',
                'data_inicio': ts,
                'valor_consulta': _valor_consulta(appointment),
                'loja_id': appointment.loja_id,
            },
        )
        if not created:
            consulta.status = 'IN_PROGRESS'
            if not consulta.data_inicio:
                consulta.data_inicio = ts
            consulta.save(update_fields=['status', 'data_inicio', 'updated_at'])
        return consulta

    if new_status == 'COMPLETED':
        try:
            consulta = appointment.consulta
        except Consulta.DoesNotExist:
            consulta = Consulta.objects.create(
                appointment=appointment,
                patient_id=appointment.patient_id,
                professional_id=appointment.professional_id,
                procedure_id=appointment.procedure_id,
                status='COMPLETED',
                data_inicio=ts,
                data_fim=ts,
                valor_consulta=_valor_consulta(appointment),
                loja_id=appointment.loja_id,
            )
            return consulta
        consulta.status = 'COMPLETED'
        if not consulta.data_inicio:
            consulta.data_inicio = ts
        consulta.data_fim = ts
        consulta.save(update_fields=['status', 'data_inicio', 'data_fim', 'updated_at'])
        return consulta

    if new_status in ('CANCELLED', 'NO_SHOW'):
        try:
            consulta = appointment.consulta
        except Consulta.DoesNotExist:
            return None
        consulta.status = 'CANCELLED'
        consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    return None
