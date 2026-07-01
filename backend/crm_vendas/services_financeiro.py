"""Serviço financeiro CRM — grupos padrão e sincronização de comissão."""
from __future__ import annotations

import logging
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)

GRUPOS_PADRAO = (
    ('receita', 'Comissão de vendas', 1),
    ('receita', 'Bonificação', 2),
    ('receita', 'Outras receitas', 99),
    ('despesa', 'Transporte', 1),
    ('despesa', 'Alimentação', 2),
    ('despesa', 'Marketing pessoal', 3),
    ('despesa', 'Outras despesas', 99),
)


def garantir_grupos_padrao(loja_id: int) -> None:
    from .models.financeiro import GrupoFinanceiroCRM

    for tipo, nome, ordem in GRUPOS_PADRAO:
        GrupoFinanceiroCRM.objects.get_or_create(
            loja_id=loja_id,
            tipo=tipo,
            nome=nome,
            defaults={'ordem': ordem, 'is_active': True},
        )


def _grupo_comissao(loja_id: int):
    from .models.financeiro import GrupoFinanceiroCRM

    garantir_grupos_padrao(loja_id)
    return GrupoFinanceiroCRM.objects.filter(
        loja_id=loja_id,
        tipo=GrupoFinanceiroCRM.TIPO_RECEITA,
        nome='Comissão de vendas',
        is_active=True,
    ).first()


def sincronizar_receita_comissao_oportunidade(oportunidade) -> None:
    """
    Cria ou atualiza receita automática quando oportunidade é ganha com comissão.
    Cancela se voltar a aberta/perdida ou comissão zerada.
    """
    from .models.financeiro import LancamentoFinanceiroCRM

    loja_id = oportunidade.loja_id
    if not loja_id or not oportunidade.vendedor_id:
        return

    existente = (
        LancamentoFinanceiroCRM.objects.filter(
            loja_id=loja_id,
            oportunidade_id=oportunidade.id,
            origem=LancamentoFinanceiroCRM.ORIGEM_COMISSAO,
        ).first()
    )

    if oportunidade.etapa != 'closed_won':
        if existente and existente.status != LancamentoFinanceiroCRM.STATUS_CANCELADO:
            existente.status = LancamentoFinanceiroCRM.STATUS_CANCELADO
            existente.save(update_fields=['status', 'updated_at'])
        return

    valor = Decimal(str(oportunidade.valor_comissao or 0))
    if valor <= 0:
        if existente and existente.status != LancamentoFinanceiroCRM.STATUS_CANCELADO:
            existente.status = LancamentoFinanceiroCRM.STATUS_CANCELADO
            existente.save(update_fields=['status', 'updated_at'])
        return

    grupo = _grupo_comissao(loja_id)
    data_ref = (
        oportunidade.data_fechamento_ganho
        or oportunidade.data_fechamento
        or timezone.now().date()
    )
    titulo = f'Comissão — {oportunidade.titulo or f"Oportunidade #{oportunidade.id}"}'

    if existente:
        existente.valor = valor
        existente.descricao = titulo[:200]
        existente.data_vencimento = data_ref
        existente.vendedor_id = oportunidade.vendedor_id
        if grupo:
            existente.grupo = grupo
        if existente.status == LancamentoFinanceiroCRM.STATUS_CANCELADO:
            existente.status = LancamentoFinanceiroCRM.STATUS_PENDENTE
        existente.save()
        return

    LancamentoFinanceiroCRM.objects.create(
        loja_id=loja_id,
        vendedor_id=oportunidade.vendedor_id,
        grupo=grupo,
        tipo=LancamentoFinanceiroCRM.TIPO_RECEITA,
        origem=LancamentoFinanceiroCRM.ORIGEM_COMISSAO,
        descricao=titulo[:200],
        valor=valor,
        status=LancamentoFinanceiroCRM.STATUS_PENDENTE,
        data_vencimento=data_ref,
        oportunidade_id=oportunidade.id,
    )
    logger.info(
        'Receita comissão criada oportunidade_id=%s vendedor_id=%s valor=%s',
        oportunidade.id,
        oportunidade.vendedor_id,
        valor,
    )


def resumo_financeiro_crm(loja_id: int, vendedor_id: int | None = None) -> dict:
    from django.db.models import Q, Sum

    from .models.financeiro import LancamentoFinanceiroCRM

    qs = LancamentoFinanceiroCRM.objects.filter(loja_id=loja_id).exclude(
        status=LancamentoFinanceiroCRM.STATUS_CANCELADO,
    )
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)

    def agg(tipo: str, status: str | None = None):
        q = qs.filter(tipo=tipo)
        if status:
            q = q.filter(status=status)
        return float(q.aggregate(t=Sum('valor'))['t'] or 0)

    receitas_pagas = agg(LancamentoFinanceiroCRM.TIPO_RECEITA, LancamentoFinanceiroCRM.STATUS_PAGO)
    receitas_pendentes = agg(LancamentoFinanceiroCRM.TIPO_RECEITA, LancamentoFinanceiroCRM.STATUS_PENDENTE)
    despesas_pagas = agg(LancamentoFinanceiroCRM.TIPO_DESPESA, LancamentoFinanceiroCRM.STATUS_PAGO)
    despesas_pendentes = agg(LancamentoFinanceiroCRM.TIPO_DESPESA, LancamentoFinanceiroCRM.STATUS_PENDENTE)

    comissao_auto = float(
        qs.filter(
            tipo=LancamentoFinanceiroCRM.TIPO_RECEITA,
            origem=LancamentoFinanceiroCRM.ORIGEM_COMISSAO,
        ).aggregate(t=Sum('valor'))['t'] or 0
    )

    return {
        'receitas_pagas': receitas_pagas,
        'receitas_pendentes': receitas_pendentes,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'saldo_realizado': receitas_pagas - despesas_pagas,
        'saldo_previsto': (receitas_pagas + receitas_pendentes) - (despesas_pagas + despesas_pendentes),
        'comissao_vendas_total': comissao_auto,
    }
