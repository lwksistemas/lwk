from .messages import MSG_PACIENTE_CONSULTA_EM_ANDAMENTO


def validar_paciente_sem_consulta_em_andamento(patient_id, *, exclude_consulta_id=None):
    """Impede duas consultas IN_PROGRESS para o mesmo paciente."""
    from clinica_beleza import consulta_service

    qs = consulta_service.Consulta.objects.filter(patient_id=patient_id, status="IN_PROGRESS")
    if exclude_consulta_id:
        qs = qs.exclude(pk=exclude_consulta_id)
    if qs.exists():
        raise ValueError(MSG_PACIENTE_CONSULTA_EM_ANDAMENTO)
