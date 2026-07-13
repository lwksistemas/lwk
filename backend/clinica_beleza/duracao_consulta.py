"""Cálculo de duração de agendamentos — tempo base do profissional vs procedimentos."""


def tempo_consulta_base_minutos(professional=None, local_atendimento=None) -> int:
    """Tempo padrão de consulta: profissional > local de atendimento (legado) > 30 min.
    Configurado em Profissionais → Ações → Tempo da consulta.
    """
    if professional is not None:
        prof_tempo = getattr(professional, "tempo_consulta_minutos", None)
        if prof_tempo and int(prof_tempo) > 0:
            return int(prof_tempo)
    if local_atendimento is not None:
        local_tempo = getattr(local_atendimento, "tempo_consulta_minutos", None)
        if local_tempo and int(local_tempo) > 0:
            return int(local_tempo)
    return 30


def calcular_duracao_novo_agendamento(
    *,
    professional,
    procedures_list=None,
    procedure=None,
    local_atendimento=None,
) -> int:
    """Duração ao criar agendamento.
    Com procedimentos: max(soma procedimentos, tempo base do profissional/local).
    Sem procedimentos: tempo base do profissional/local.
    """
    base = tempo_consulta_base_minutos(professional, local_atendimento)
    if procedures_list:
        proc_total = sum(int(p.duracao_minutos) for p in procedures_list)
        if proc_total > 0:
            return max(proc_total, base)
        return base
    if procedure is not None:
        proc_total = int(procedure.duracao_minutos)
        return max(proc_total, base) if proc_total > 0 else base
    return base


def calcular_duracao_efetiva_agendamento(
    *,
    duracao_manual=None,
    professional,
    local_atendimento=None,
    appointment_procedures=None,
    procedure_principal=None,
) -> int:
    """Duração efetiva de um agendamento existente (sem override manual).
    """
    if duracao_manual is not None:
        return int(duracao_manual)

    proc_total = 0
    if appointment_procedures is not None:
        proc_total = sum(ap.get_duracao() for ap in appointment_procedures)
    elif procedure_principal is not None:
        proc_total = int(procedure_principal.duracao_minutos)

    base = tempo_consulta_base_minutos(professional, local_atendimento)
    if proc_total > 0:
        return max(proc_total, base)
    return base
