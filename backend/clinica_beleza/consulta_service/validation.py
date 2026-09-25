from .messages import (
    MSG_PACIENTE_CONSULTA_EM_ANDAMENTO,
    MSG_PROFISSIONAL_LOCAL_EM_ANDAMENTO,
    MSG_PROFISSIONAL_OBRIGATORIO,
)


def local_id_efetivo_consulta(consulta) -> int | None:
    """Local da consulta, com fallback para o agendamento."""
    local_id = getattr(consulta, "local_atendimento_id", None)
    if local_id:
        return local_id
    appointment = getattr(consulta, "appointment", None)
    return getattr(appointment, "local_atendimento_id", None) if appointment is not None else None


def validar_paciente_sem_consulta_em_andamento(patient_id, *, exclude_consulta_id=None):
    """Impede duas consultas IN_PROGRESS para o mesmo paciente."""
    from clinica_beleza import consulta_service

    qs = consulta_service.Consulta.objects.filter(patient_id=patient_id, status="IN_PROGRESS")
    if exclude_consulta_id:
        qs = qs.exclude(pk=exclude_consulta_id)
    if qs.exists():
        raise ValueError(MSG_PACIENTE_CONSULTA_EM_ANDAMENTO)


def validar_profissional_livre_no_local(professional_id, local_id, *, exclude_consulta_id=None):
    """Exige profissional e impede dois atendimentos no mesmo local.

    Outro local de atendimento pode iniciar em paralelo.
    """
    from django.db.models.functions import Coalesce

    from clinica_beleza import consulta_service

    if not professional_id:
        raise ValueError(MSG_PROFISSIONAL_OBRIGATORIO)
    qs = (
        consulta_service.Consulta.objects.filter(
            professional_id=professional_id,
            status="IN_PROGRESS",
        )
        .annotate(
            local_efetivo=Coalesce("local_atendimento_id", "appointment__local_atendimento_id"),
        )
        .filter(local_efetivo=local_id)
    )
    if exclude_consulta_id:
        qs = qs.exclude(pk=exclude_consulta_id)
    if qs.exists():
        raise ValueError(MSG_PROFISSIONAL_LOCAL_EM_ANDAMENTO)
