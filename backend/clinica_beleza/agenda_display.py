"""Exibição de data/hora de agendamentos no fuso da clínica."""
from django.utils import timezone


def local_appointment_dt(value):
    """Datetime do agendamento no fuso configurado (ex.: America/Sao_Paulo)."""
    dt = value.date if hasattr(value, "date") else value
    return timezone.localtime(dt)


def format_agenda_data(value) -> str:
    return local_appointment_dt(value).strftime("%d/%m/%Y")


def format_agenda_hora(value) -> str:
    return local_appointment_dt(value).strftime("%H:%M")
