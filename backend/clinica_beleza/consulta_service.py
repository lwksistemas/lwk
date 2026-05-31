"""
Sincronização de Consulta com mudanças de status do agendamento na agenda.
A consulta só é criada/atualizada quando o status muda na agenda — não manualmente na listagem.
"""
import logging
from decimal import Decimal

from django.utils.timezone import now

from .models import Appointment, Consulta, Payment

logger = logging.getLogger(__name__)


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


def _ensure_payment_for_appointment(appointment, consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """Garante lançamento financeiro do atendimento (cria ou atualiza)."""
    payment = Payment.objects.filter(appointment=appointment).first()
    valor = amount if amount is not None else (consulta.valor_consulta or _valor_consulta(appointment))
    if isinstance(valor, (int, float, str)):
        valor = Decimal(str(valor))

    if not payment:
        return Payment.objects.create(
            appointment=appointment,
            amount=valor,
            payment_method=payment_method or 'CASH',
            status='PAID' if mark_as_paid else 'PENDING',
            payment_date=now() if mark_as_paid else None,
            loja_id=appointment.loja_id,
        )

    if payment_method:
        payment.payment_method = payment_method
    if amount is not None:
        payment.amount = valor
    if mark_as_paid:
        payment.status = 'PAID'
        if not payment.payment_date:
            payment.payment_date = now()
    payment.save()
    return payment


def iniciar_consulta(consulta):
    """
    Profissional inicia atendimento: consulta → IN_PROGRESS, agenda → IN_PROGRESS, data_inicio.
    """
    appointment = consulta.appointment
    if consulta.status != 'SCHEDULED':
        raise ValueError('A consulta precisa estar agendada para ser iniciada.')
    if appointment.status not in ('CONFIRMED', 'SCHEDULED'):
        raise ValueError('Confirme o agendamento na agenda antes de iniciar a consulta.')

    old_status = appointment.status
    ts = now()

    appointment.status = 'IN_PROGRESS'
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=['status', 'version', 'updated_at'])

    consulta.status = 'IN_PROGRESS'
    consulta.data_inicio = ts
    consulta.save(update_fields=['status', 'data_inicio', 'updated_at'])

    sync_consulta_from_appointment_status(appointment, 'IN_PROGRESS', old_status)
    consulta.refresh_from_db()
    return consulta


def finalizar_consulta(consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """
    Finaliza consulta clínica: agenda → COMPLETED, consulta concluída e lançamento financeiro.
    """
    from rules.base import MotorRegras

    appointment = consulta.appointment
    old_status = appointment.status

    if consulta.status == 'COMPLETED':
        if appointment.status != 'COMPLETED':
            appointment.status = 'COMPLETED'
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=['status', 'version', 'updated_at'])
            sync_consulta_from_appointment_status(appointment, 'COMPLETED', old_status)
        try:
            MotorRegras().executar('AGENDAMENTO_FINALIZADO', {'appointment': appointment})
        except Exception:
            logger.exception('Erro ao executar regra financeira (consulta %s)', consulta.id)
        _ensure_payment_for_appointment(
            appointment, consulta,
            payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
        )
        consulta.refresh_from_db()
        return consulta

    if consulta.status != 'IN_PROGRESS':
        raise ValueError('Inicie a consulta antes de finalizar.')

    appointment.status = 'COMPLETED'
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=['status', 'version', 'updated_at'])

    sync_consulta_from_appointment_status(appointment, 'COMPLETED', old_status)

    try:
        MotorRegras().executar('AGENDAMENTO_FINALIZADO', {'appointment': appointment})
    except Exception:
        logger.exception('Erro ao executar regra financeira (consulta %s)', consulta.id)

    _ensure_payment_for_appointment(
        appointment, consulta,
        payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
    )
    consulta.refresh_from_db()
    return consulta
