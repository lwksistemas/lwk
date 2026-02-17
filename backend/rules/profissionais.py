"""
Regras de profissionais: horário, folgas, limite de atendimentos por dia.
Respeitado indiretamente via BloqueioHorario; aqui podem ser adicionadas
regras extras (ex.: limite de N atendimentos/dia por profissional).
"""
from django.core.exceptions import ValidationError

from clinica_beleza.models import Appointment


# Limite máximo de atendimentos por profissional por dia (pode vir de config/RegraAutomatica no futuro)
LIMITE_ATENDIMENTOS_POR_DIA = 20


def limite_atendimentos_dia(contexto):
    """
    Impede agendar além de N atendimentos no mesmo dia para o mesmo profissional.
    contexto: profissional, date, date_end, appointment_id (opcional)
    """
    profissional = contexto.get("profissional")
    date_start = contexto.get("date")
    appointment_id = contexto.get("appointment_id")

    if not profissional or not date_start:
        return

    # Conta agendamentos do profissional naquele dia (excluindo o que está sendo editado)
    base = Appointment.objects.filter(
        professional=profissional,
        date__date=date_start.date(),
    ).exclude(pk=appointment_id or 0)

    if base.count() >= LIMITE_ATENDIMENTOS_POR_DIA:
        raise ValidationError(
            f"Limite de {LIMITE_ATENDIMENTOS_POR_DIA} atendimentos por dia para este profissional foi atingido."
        )


regras_profissionais = [
    {
        "evento": "AGENDAMENTO_CRIADO",
        "acao": limite_atendimentos_dia,
        "ativa": True,
    },
    {
        "evento": "AGENDAMENTO_ATUALIZADO",
        "acao": limite_atendimentos_dia,
        "ativa": True,
    },
]
