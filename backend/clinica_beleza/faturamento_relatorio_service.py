"""
Service para relatório de faturamento — Clínica da Beleza.

Agrupa receita por profissional, procedimento, local de atendimento ou convênio.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Literal, Optional

from django.db.models import Q, Sum, Count

from .models import Appointment, AppointmentProcedure, Payment


AgrupamentoType = Literal['profissional', 'procedimento', 'local', 'convenio']


def calcular_faturamento(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    agrupar: AgrupamentoType = 'profissional',
) -> dict:
    """
    Calcula faturamento da clínica agrupado pelo critério selecionado.

    Retorna dict com 'linhas' (lista) e 'totais'.
    """
    # Filtrar consultas pagas no período
    filters = Q(status='COMPLETED') | Q(status='PAID')
    if data_inicio:
        filters &= Q(date__gte=data_inicio)
    if data_fim:
        filters &= Q(date__lte=data_fim)

    appointments = Appointment.objects.filter(filters).select_related(
        'professional', 'patient', 'local_atendimento',
    ).prefetch_related('procedures', 'procedures__procedure', 'payments')

    # Acumular dados por grupo
    grupos: dict[str, dict] = defaultdict(lambda: {
        'nome': '',
        'total_atendimentos': 0,
        'valor_consulta': 0.0,
        'valor_procedimento': 0.0,
        'valor_total': 0.0,
    })

    for appt in appointments:
        # Determinar chave do grupo
        chave = _get_grupo_chave(appt, agrupar)
        nome = _get_grupo_nome(appt, agrupar)

        grupo = grupos[chave]
        grupo['nome'] = nome
        grupo['total_atendimentos'] += 1

        # Valor da consulta (price do appointment)
        valor_consulta = float(appt.price or 0)
        grupo['valor_consulta'] += valor_consulta

        # Valor dos procedimentos
        valor_proc = 0.0
        for ap in appt.procedures.all():
            valor_proc += float(ap.price or 0)
        grupo['valor_procedimento'] += valor_proc

        grupo['valor_total'] += valor_consulta + valor_proc

    # Converter para lista ordenada por valor total desc
    linhas = sorted(grupos.values(), key=lambda x: x['valor_total'], reverse=True)

    # Calcular totais
    totais = {
        'total_atendimentos': sum(l['total_atendimentos'] for l in linhas),
        'valor_consulta': sum(l['valor_consulta'] for l in linhas),
        'valor_procedimento': sum(l['valor_procedimento'] for l in linhas),
        'valor_total': sum(l['valor_total'] for l in linhas),
    }

    return {
        'linhas': linhas,
        'totais': totais,
        'agrupamento': agrupar,
    }


def _get_grupo_chave(appt: Appointment, agrupar: AgrupamentoType) -> str:
    """Retorna chave única para agrupamento."""
    if agrupar == 'profissional':
        return f'prof_{appt.professional_id or 0}'
    elif agrupar == 'procedimento':
        # Agrupa pelo procedimento principal (primeiro) ou "Consulta"
        procs = list(appt.procedures.all())
        if procs:
            return f'proc_{procs[0].procedure_id or 0}'
        return 'proc_consulta'
    elif agrupar == 'local':
        local = getattr(appt, 'local_atendimento', None)
        return f'local_{local.id if local else 0}'
    elif agrupar == 'convenio':
        patient = appt.patient
        conv_id = getattr(patient, 'convenio_id', None) or 0
        return f'conv_{conv_id}'
    return 'outros'


def _get_grupo_nome(appt: Appointment, agrupar: AgrupamentoType) -> str:
    """Retorna nome legível para o grupo."""
    if agrupar == 'profissional':
        prof = appt.professional
        return getattr(prof, 'nome', '') or getattr(prof, 'name', '') or 'Sem profissional'
    elif agrupar == 'procedimento':
        procs = list(appt.procedures.all())
        if procs:
            proc = procs[0].procedure
            return getattr(proc, 'nome', '') or getattr(proc, 'name', '') or 'Procedimento'
        return 'Consulta (sem procedimento)'
    elif agrupar == 'local':
        local = getattr(appt, 'local_atendimento', None)
        if local:
            return getattr(local, 'nome', '') or getattr(local, 'name', '') or 'Local sem nome'
        return 'Sem local definido'
    elif agrupar == 'convenio':
        patient = appt.patient
        conv_name = getattr(patient, 'convenio_name', None)
        if conv_name:
            return conv_name
        # Tentar via FK
        convenio = getattr(patient, 'convenio', None)
        if convenio and hasattr(convenio, 'nome'):
            return convenio.nome
        return 'Particular'
    return 'Outros'
