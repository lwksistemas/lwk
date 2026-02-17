"""
Regras de agenda: conflitos de horário, bloqueios, horário comercial.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError

from clinica_beleza.models import Appointment


def bloquear_conflitos(contexto):
    """
    Impede agendamento no mesmo horário para o mesmo profissional.
    contexto: profissional, date, date_end, appointment_id (opcional, para update)
    """
    profissional = contexto.get("profissional")
    date_start = contexto.get("date")
    date_end = contexto.get("date_end")
    appointment_id = contexto.get("appointment_id")

    if not profissional or not date_start or not date_end:
        return

    # Outros agendamentos do mesmo profissional no mesmo dia
    outros = (
        Appointment.objects.filter(
            professional=profissional,
            date__date=date_start.date(),
        )
        .exclude(pk=appointment_id or 0)
        .select_related("procedure")
    )
    for outro in outros:
        o_end = outro.date + timedelta(minutes=outro.procedure.duration)
        if date_start < o_end and date_end > outro.date:
            raise ValidationError("Horário já ocupado para este profissional.")


regras_agenda = [
    {
        "evento": "AGENDAMENTO_CRIADO",
        "acao": bloquear_conflitos,
        "ativa": True,
    },
    {
        "evento": "AGENDAMENTO_ATUALIZADO",
        "acao": bloquear_conflitos,
        "ativa": True,
    },
]
