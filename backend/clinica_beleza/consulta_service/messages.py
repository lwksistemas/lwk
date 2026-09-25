MSG_CONSULTA_CONCLUIDA_NAO_EXCLUI = "Consultas concluídas não podem ser excluídas."
MSG_PACIENTE_CONSULTA_EM_ANDAMENTO = (
    "Este paciente já possui uma consulta em andamento. Finalize-a antes de iniciar outra."
)
MSG_PROFISSIONAL_OBRIGATORIO = "Selecione o profissional."
MSG_PROFISSIONAL_LOCAL_EM_ANDAMENTO = (
    "Este profissional já está em atendimento neste local. "
    "Finalize essa consulta ou inicie em outro local de atendimento."
)


def consulta_esta_concluida(consulta) -> bool:
    """True se a consulta já foi finalizada (status, data_fim ou agenda concluída)."""
    if consulta.status == "COMPLETED":
        return True
    if consulta.data_fim:
        return True
    appointment = getattr(consulta, "appointment", None)
    return bool(appointment and appointment.status == "COMPLETED")


def motivo_bloqueio_exclusao_consulta(consulta) -> str | None:
    if consulta_esta_concluida(consulta):
        return MSG_CONSULTA_CONCLUIDA_NAO_EXCLUI
    return None
