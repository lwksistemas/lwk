"""
Intervalos de data e filtros de período unificados para o CRM Vendas.

Fonte única para dashboard, relatórios PDF, financeiro e comissão.
"""
from __future__ import annotations

import calendar
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

PERIODOS_PIPELINE_CRIACAO_ESTRITA = frozenset({
    'mes_atual', 'mes_passado', 'hoje', 'ontem', 'semana_atual', 'semana_passada', 'personalizado',
})


def inicio_trimestre_rolante(hoje):
    """Início do trimestre rolante: mês atual + 2 meses anteriores (ex.: jul → mai/1)."""
    mes = hoje.month - 2
    ano = hoje.year
    while mes <= 0:
        mes += 12
        ano -= 1
    return hoje.replace(year=ano, month=mes, day=1)


def calcular_intervalo_datas(periodo, data_inicio_param=None, data_fim_param=None):
    """Calcula intervalo de datas baseado no período selecionado."""
    hoje = timezone.now().date()
    if periodo == 'personalizado' and data_inicio_param and data_fim_param:
        try:
            from datetime import datetime
            return (
                datetime.strptime(data_inicio_param, '%Y-%m-%d').date(),
                datetime.strptime(data_fim_param, '%Y-%m-%d').date(),
            )
        except (ValueError, TypeError):
            pass
    if periodo == 'hoje':
        return hoje, hoje
    if periodo == 'ontem':
        ontem = hoje - timedelta(days=1)
        return ontem, ontem
    if periodo == 'semana_atual':
        inicio = hoje - timedelta(days=hoje.weekday())
        return inicio, hoje
    if periodo == 'semana_passada':
        fim = hoje - timedelta(days=hoje.weekday() + 1)
        inicio = fim - timedelta(days=6)
        return inicio, fim
    if periodo == 'mes_passado':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
        primeiro_dia_mes_passado = ultimo_dia_mes_passado.replace(day=1)
        return primeiro_dia_mes_passado, ultimo_dia_mes_passado
    if periodo == 'trimestre_atual':
        return inicio_trimestre_rolante(hoje), hoje
    if periodo == 'ultimos_30_dias':
        return hoje - timedelta(days=30), hoje
    if periodo == 'ultimos_90_dias':
        return hoje - timedelta(days=90), hoje
    if periodo in ('este_ano', 'ano_atual'):
        return hoje.replace(month=1, day=1), hoje
    # mes_atual (padrão)
    return hoje.replace(day=1), hoje


def calcular_intervalo_vencimento(periodo, data_inicio=None, data_fim=None):
    """
    Intervalo para filtrar data_vencimento.

    Diferente do dashboard (até hoje), vencimentos no mês/semana/trimestre atuais
    incluem datas futuras dentro do período calendário.
    """
    inicio, fim = calcular_intervalo_datas(periodo, data_inicio, data_fim)
    hoje = timezone.now().date()

    if periodo == 'mes_atual':
        ultimo_dia = calendar.monthrange(inicio.year, inicio.month)[1]
        fim = inicio.replace(day=ultimo_dia)
    elif periodo == 'semana_atual':
        fim = inicio + timedelta(days=6)
    elif periodo == 'trimestre_atual':
        mes_fim_trimestre = ((hoje.month - 1) // 3 + 1) * 3
        ultimo_dia = calendar.monthrange(hoje.year, mes_fim_trimestre)[1]
        fim = hoje.replace(month=mes_fim_trimestre, day=ultimo_dia)
    elif periodo in ('este_ano', 'ano_atual'):
        fim = hoje.replace(month=12, day=31)

    return inicio, fim


def filtro_fechamento_no_periodo(data_inicio, data_fim, prefix=''):
    """Filtro Q para oportunidades fechadas no período (com ou sem data_fechamento_ganho).

    Prioridade: data_fechamento_ganho > data_fechamento > created_at.
    """
    p = f'{prefix}__' if prefix else ''
    return (
        Q(**{f'{p}data_fechamento_ganho__gte': data_inicio, f'{p}data_fechamento_ganho__lte': data_fim})
        | (
            Q(**{f'{p}data_fechamento_ganho__isnull': True})
            & Q(**{f'{p}data_fechamento__gte': data_inicio, f'{p}data_fechamento__lte': data_fim})
        )
        | (
            Q(**{f'{p}data_fechamento_ganho__isnull': True})
            & Q(**{f'{p}data_fechamento__isnull': True})
            & Q(**{f'{p}created_at__date__gte': data_inicio, f'{p}created_at__date__lte': data_fim})
        )
    )
