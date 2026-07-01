"""Recorrências financeiras CRM — geração automática de lançamentos."""
from __future__ import annotations

import calendar
import logging
from datetime import date
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)


def _adicionar_periodo(data: date, frequencia: str) -> date:
    if frequencia == 'trimestral':
        mes = data.month + 3
        ano = data.year + (mes - 1) // 12
        mes = ((mes - 1) % 12) + 1
        dia = min(data.day, calendar.monthrange(ano, mes)[1])
        return date(ano, mes, dia)
    if frequencia == 'anual':
        ano = data.year + 1
        dia = min(data.day, calendar.monthrange(ano, data.month)[1])
        return date(ano, data.month, dia)
    # mensal
    mes = data.month + 1
    ano = data.year + (mes - 1) // 12
    mes = ((mes - 1) % 12) + 1
    dia = min(data.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def criar_recorrencia_com_primeiro_lancamento(
    loja_id: int,
    *,
    vendedor_id: int,
    tipo: str,
    descricao: str,
    valor,
    data_vencimento: date,
    frequencia: str = 'mensal',
    data_fim=None,
    grupo=None,
    observacoes: str = '',
    status: str = 'pendente',
    data_pagamento=None,
) -> tuple:
    """Cria recorrência e o primeiro lançamento manual vinculado."""
    from .models.financeiro import LancamentoFinanceiroCRM, RecorrenciaFinanceiroCRM

    proximo = _adicionar_periodo(data_vencimento, frequencia)
    rec = RecorrenciaFinanceiroCRM.objects.create(
        loja_id=loja_id,
        vendedor_id=vendedor_id,
        grupo=grupo,
        tipo=tipo,
        descricao=descricao[:200],
        valor=Decimal(str(valor)),
        frequencia=frequencia,
        proximo_vencimento=proximo,
        data_fim=data_fim,
        observacoes=observacoes or '',
        is_active=True,
    )
    lanc = LancamentoFinanceiroCRM.objects.create(
        loja_id=loja_id,
        vendedor_id=vendedor_id,
        grupo=grupo,
        tipo=tipo,
        origem=LancamentoFinanceiroCRM.ORIGEM_MANUAL,
        descricao=descricao[:200],
        valor=Decimal(str(valor)),
        status=status,
        data_vencimento=data_vencimento,
        data_pagamento=data_pagamento,
        observacoes=observacoes or '',
        recorrencia=rec,
    )
    return rec, lanc


def processar_recorrencias_pendentes(loja_id: int | None = None, *, dry_run: bool = False) -> dict:
    """Gera lançamentos pendentes para recorrências com vencimento <= hoje."""
    from .models.financeiro import LancamentoFinanceiroCRM, RecorrenciaFinanceiroCRM

    hoje = timezone.now().date()
    qs = RecorrenciaFinanceiroCRM.objects.filter(is_active=True, proximo_vencimento__lte=hoje)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    criadas = ignoradas = encerradas = 0
    for rec in qs.select_related('grupo', 'vendedor').order_by('id'):
        if rec.data_fim and rec.proximo_vencimento > rec.data_fim:
            if not dry_run:
                rec.is_active = False
                rec.save(update_fields=['is_active', 'updated_at'])
            encerradas += 1
            continue

        existe = LancamentoFinanceiroCRM.objects.filter(
            loja_id=rec.loja_id,
            recorrencia_id=rec.id,
            data_vencimento=rec.proximo_vencimento,
        ).exists()
        if existe:
            ignoradas += 1
        elif not dry_run:
            LancamentoFinanceiroCRM.objects.create(
                loja_id=rec.loja_id,
                vendedor_id=rec.vendedor_id,
                grupo=rec.grupo,
                tipo=rec.tipo,
                origem=LancamentoFinanceiroCRM.ORIGEM_RECORRENCIA,
                descricao=rec.descricao,
                valor=rec.valor,
                status=LancamentoFinanceiroCRM.STATUS_PENDENTE,
                data_vencimento=rec.proximo_vencimento,
                observacoes=rec.observacoes,
                recorrencia=rec,
            )
            criadas += 1
        else:
            criadas += 1

        proximo = _adicionar_periodo(rec.proximo_vencimento, rec.frequencia)
        if rec.data_fim and proximo > rec.data_fim:
            if not dry_run:
                rec.is_active = False
                rec.proximo_vencimento = proximo
                rec.save(update_fields=['is_active', 'proximo_vencimento', 'updated_at'])
            encerradas += 1
        elif not dry_run:
            rec.proximo_vencimento = proximo
            rec.save(update_fields=['proximo_vencimento', 'updated_at'])

    return {
        'criadas': criadas,
        'ignoradas': ignoradas,
        'encerradas': encerradas,
        'dry_run': dry_run,
    }
