"""
Regras de profissionais: horário de trabalho, folgas, limite de atendimentos por dia.
"""
from django.core.exceptions import ValidationError

from clinica_beleza.models import Appointment, HorarioTrabalhoProfissional


# Limite máximo de atendimentos por profissional por dia (pode vir de config/RegraAutomatica no futuro)
LIMITE_ATENDIMENTOS_POR_DIA = 20


def validar_horario_trabalho(contexto):
    """
    Impede agendar fora do horário de trabalho configurado do profissional.
    contexto: profissional, date, date_end
    """
    profissional = contexto.get("profissional")
    date_start = contexto.get("date")
    date_end = contexto.get("date_end")

    if not profissional or not date_start or not date_end:
        return

    horarios = HorarioTrabalhoProfissional.objects.filter(professional=profissional, ativo=True)
    if not horarios.exists():
        return

    dia_semana = date_start.weekday()  # 0=segunda … 6=domingo (igual ao model)
    try:
        horario = horarios.get(dia_semana=dia_semana)
    except HorarioTrabalhoProfissional.DoesNotExist:
        raise ValidationError("Profissional não trabalha neste dia da semana.")

    t_start = date_start.time()
    t_end = date_end.time()

    if t_start < horario.hora_entrada:
        raise ValidationError(
            f"Horário antes do expediente ({horario.hora_entrada.strftime('%H:%M')})."
        )
    if t_end > horario.hora_saida:
        raise ValidationError(
            f"Horário após o fim do expediente ({horario.hora_saida.strftime('%H:%M')})."
        )

    if horario.intervalo_inicio and horario.intervalo_fim:
        if t_start < horario.intervalo_fim and t_end > horario.intervalo_inicio:
            raise ValidationError(
                "Horário conflita com o intervalo do profissional "
                f"({horario.intervalo_inicio.strftime('%H:%M')}–{horario.intervalo_fim.strftime('%H:%M')})."
            )


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
        "acao": validar_horario_trabalho,
        "ativa": True,
    },
    {
        "evento": "AGENDAMENTO_ATUALIZADO",
        "acao": validar_horario_trabalho,
        "ativa": True,
    },
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
