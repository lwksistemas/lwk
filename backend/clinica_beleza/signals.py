"""Sinais — invalidação de cache do dashboard."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Appointment, AppointmentProcedure, Consulta, Payment
from .utils import invalidate_dashboard_cache


def _invalidate_from_payment(payment):
    if not payment.loja_id:
        return
    mes, ano = None, None
    if payment.payment_date:
        d = payment.payment_date.date()
        mes, ano = d.month, d.year
    invalidate_dashboard_cache(payment.loja_id, mes=mes, ano=ano)


def _invalidate_from_appointment(appt):
    if not appt.loja_id:
        return
    d = appt.date.date() if appt.date else None
    invalidate_dashboard_cache(
        appt.loja_id,
        mes=d.month if d else None,
        ano=d.year if d else None,
        professional_id=appt.professional_id,
    )


@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def payment_dashboard_cache(sender, instance, **kwargs):
    _invalidate_from_payment(instance)


@receiver(post_save, sender=Consulta)
def consulta_dashboard_cache(sender, instance, **kwargs):
    if not instance.loja_id:
        return
    ref = instance.data_fim or instance.updated_at or (
        instance.appointment.date if instance.appointment_id else None
    )
    mes, ano = None, None
    if ref:
        d = ref.date() if hasattr(ref, "date") else ref
        mes, ano = d.month, d.year
    invalidate_dashboard_cache(
        instance.loja_id,
        mes=mes,
        ano=ano,
        professional_id=instance.professional_id,
    )


@receiver(post_save, sender=Appointment)
@receiver(post_delete, sender=Appointment)
def appointment_dashboard_cache(sender, instance, **kwargs):
    _invalidate_from_appointment(instance)


@receiver(post_save, sender=AppointmentProcedure)
@receiver(post_delete, sender=AppointmentProcedure)
def appointment_procedure_dashboard_cache(sender, instance, **kwargs):
    if instance.appointment_id:
        try:
            appt = instance.appointment
        except Appointment.DoesNotExist:
            return
        _invalidate_from_appointment(appt)
