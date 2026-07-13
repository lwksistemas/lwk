"""Serviço financeiro CRM — grupos padrão e sincronização de comissão."""
from __future__ import annotations

import logging
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)

GRUPOS_PADRAO = (
    ("receita", "Comissão de vendas", 1),
    ("receita", "Bonificação", 2),
    ("receita", "Outras receitas", 99),
    ("despesa", "Transporte", 1),
    ("despesa", "Alimentação", 2),
    ("despesa", "Marketing pessoal", 3),
    ("despesa", "Outras despesas", 99),
)


def garantir_grupos_padrao(loja_id: int) -> None:
    from .models.financeiro import GrupoFinanceiroCRM

    for tipo, nome, ordem in GRUPOS_PADRAO:
        GrupoFinanceiroCRM.objects.get_or_create(
            loja_id=loja_id,
            tipo=tipo,
            nome=nome,
            defaults={"ordem": ordem, "is_active": True},
        )


def _grupo_comissao(loja_id: int):
    from .models.financeiro import GrupoFinanceiroCRM

    garantir_grupos_padrao(loja_id)
    return GrupoFinanceiroCRM.objects.filter(
        loja_id=loja_id,
        tipo=GrupoFinanceiroCRM.TIPO_RECEITA,
        nome="Comissão de vendas",
        is_active=True,
    ).first()


def sincronizar_receita_comissao_oportunidade(oportunidade) -> None:
    """Cria ou atualiza receita automática quando oportunidade é ganha com comissão.
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

    if oportunidade.etapa != "closed_won":
        if existente and existente.status != LancamentoFinanceiroCRM.STATUS_CANCELADO:
            existente.status = LancamentoFinanceiroCRM.STATUS_CANCELADO
            existente.save(update_fields=["status", "updated_at"])
        return

    valor = Decimal(str(oportunidade.valor_comissao or 0))
    if valor <= 0:
        if existente and existente.status != LancamentoFinanceiroCRM.STATUS_CANCELADO:
            existente.status = LancamentoFinanceiroCRM.STATUS_CANCELADO
            existente.save(update_fields=["status", "updated_at"])
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
        "Receita comissão criada oportunidade_id=%s vendedor_id=%s valor=%s",
        oportunidade.id,
        oportunidade.vendedor_id,
        valor,
    )


def calcular_intervalo_vencimento(periodo, data_inicio=None, data_fim=None):
    from .periodo import calcular_intervalo_vencimento as _calcular_intervalo_vencimento

    return _calcular_intervalo_vencimento(periodo, data_inicio, data_fim)


def aplicar_filtro_periodo_lancamentos(queryset, *, periodo="mes_atual", data_inicio=None, data_fim=None):
    """Filtra lançamentos pelo período.

    Lógica:
    - Lançamentos PAGOS com data_pagamento: filtrados por data_pagamento (caixa).
    - Lançamentos PAGOS sem data_pagamento: filtrados por data_vencimento (fallback).
    - Lançamentos PENDENTES/outros: filtrados por data_vencimento (competência).
    """
    from django.db.models import Q

    from .models.financeiro import LancamentoFinanceiroCRM

    inicio, fim = calcular_intervalo_vencimento(periodo, data_inicio, data_fim)
    q_pago_com_data = Q(
        status=LancamentoFinanceiroCRM.STATUS_PAGO,
        data_pagamento__isnull=False,
        data_pagamento__gte=inicio,
        data_pagamento__lte=fim,
    )
    q_pago_sem_data = Q(
        status=LancamentoFinanceiroCRM.STATUS_PAGO,
        data_pagamento__isnull=True,
        data_vencimento__gte=inicio,
        data_vencimento__lte=fim,
    )
    q_pendente_no_vencimento = (
        Q(data_vencimento__gte=inicio, data_vencimento__lte=fim)
        & ~Q(status=LancamentoFinanceiroCRM.STATUS_PAGO)
    )
    return queryset.filter(q_pago_com_data | q_pago_sem_data | q_pendente_no_vencimento)


def resumo_financeiro_crm(
    loja_id: int,
    vendedor_id: int | None = None,
    *,
    periodo: str = "mes_atual",
    data_inicio=None,
    data_fim=None,
) -> dict:
    from django.db.models import Sum

    from .models import Oportunidade
    from .models.financeiro import LancamentoFinanceiroCRM
    from .periodo import calcular_intervalo_datas
    from .periodo import filtro_fechamento_no_periodo as _filtro_fechamento_no_periodo

    inicio, fim = calcular_intervalo_vencimento(periodo, data_inicio, data_fim)
    inicio_opp, fim_opp = calcular_intervalo_datas(periodo, data_inicio, data_fim)

    # Lançamentos pagos com data_pagamento: filtrados por data_pagamento (caixa)
    # Lançamentos pagos sem data_pagamento: filtrados por data_vencimento (fallback)
    # Lançamentos pendentes: filtrados por data_vencimento (competência)
    from django.db.models import Q as _Q
    _q_pago_com_data = _Q(
        status=LancamentoFinanceiroCRM.STATUS_PAGO,
        data_pagamento__isnull=False,
        data_pagamento__gte=inicio,
        data_pagamento__lte=fim,
    )
    _q_pago_sem_data = _Q(
        status=LancamentoFinanceiroCRM.STATUS_PAGO,
        data_pagamento__isnull=True,
        data_vencimento__gte=inicio,
        data_vencimento__lte=fim,
    )
    _q_pendente = (
        _Q(data_vencimento__gte=inicio, data_vencimento__lte=fim)
        & ~_Q(status=LancamentoFinanceiroCRM.STATUS_PAGO)
    )
    qs_base = LancamentoFinanceiroCRM.objects.filter(loja_id=loja_id).exclude(
        status=LancamentoFinanceiroCRM.STATUS_CANCELADO,
    ).filter(_q_pago_com_data | _q_pago_sem_data | _q_pendente)
    qs = qs_base
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)

    def agg(tipo: str, status: str | None = None):
        q = qs.filter(tipo=tipo)
        if status:
            q = q.filter(status=status)
        return float(q.aggregate(t=Sum("valor"))["t"] or 0)

    receitas_pagas = agg(LancamentoFinanceiroCRM.TIPO_RECEITA, LancamentoFinanceiroCRM.STATUS_PAGO)
    receitas_pendentes = agg(LancamentoFinanceiroCRM.TIPO_RECEITA, LancamentoFinanceiroCRM.STATUS_PENDENTE)
    despesas_pagas = agg(LancamentoFinanceiroCRM.TIPO_DESPESA, LancamentoFinanceiroCRM.STATUS_PAGO)
    despesas_pendentes = agg(LancamentoFinanceiroCRM.TIPO_DESPESA, LancamentoFinanceiroCRM.STATUS_PENDENTE)

    # Total de comissões = soma de valor_comissao das oportunidades ganhas no período
    # (mesma lógica do dashboard — não usar valor do lançamento, que pode refletir venda total)
    opp_qs = Oportunidade.objects.filter(loja_id=loja_id, etapa="closed_won").filter(
        _filtro_fechamento_no_periodo(inicio_opp, fim_opp),
    )
    if vendedor_id:
        opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
    comissao_vendas = float(opp_qs.aggregate(t=Sum("valor_comissao"))["t"] or 0)

    return {
        "receitas_pagas": receitas_pagas,
        "receitas_pendentes": receitas_pendentes,
        "despesas_pagas": despesas_pagas,
        "despesas_pendentes": despesas_pendentes,
        "saldo_realizado": receitas_pagas - despesas_pagas,
        "saldo_previsto": (receitas_pagas + receitas_pendentes) - (despesas_pagas + despesas_pendentes),
        "comissao_vendas_total": comissao_vendas,
        "periodo_inicio": inicio.isoformat(),
        "periodo_fim": fim.isoformat(),
    }


def sincronizar_comissoes_retroativas(loja_id: int, *, dry_run: bool = False) -> dict:
    """Gera receitas de comissão para oportunidades closed_won já existentes.
    Útil após ativar o módulo financeiro ou corrigir valor_comissao antigo.
    """
    from .models import Oportunidade

    garantir_grupos_padrao(loja_id)
    qs = (
        Oportunidade.objects.filter(loja_id=loja_id, etapa="closed_won")
        .exclude(vendedor_id__isnull=True)
        .exclude(valor_comissao__isnull=True)
        .exclude(valor_comissao=0)
        .select_related("vendedor")
        .order_by("id")
    )

    criadas = atualizadas = ignoradas = 0
    total = qs.count()
    for op in qs.iterator():
        from .models.financeiro import LancamentoFinanceiroCRM

        existente = LancamentoFinanceiroCRM.objects.filter(
            loja_id=loja_id,
            oportunidade_id=op.id,
            origem=LancamentoFinanceiroCRM.ORIGEM_COMISSAO,
        ).first()
        if dry_run:
            if existente:
                atualizadas += 1
            else:
                criadas += 1
            continue
        antes_id = existente.id if existente else None
        sincronizar_receita_comissao_oportunidade(op)
        existente_depois = LancamentoFinanceiroCRM.objects.filter(
            loja_id=loja_id,
            oportunidade_id=op.id,
            origem=LancamentoFinanceiroCRM.ORIGEM_COMISSAO,
        ).first()
        if not existente_depois or existente_depois.status == LancamentoFinanceiroCRM.STATUS_CANCELADO:
            ignoradas += 1
        elif antes_id:
            atualizadas += 1
        else:
            criadas += 1

    return {
        "loja_id": loja_id,
        "oportunidades_analisadas": total,
        "criadas": criadas,
        "atualizadas": atualizadas,
        "ignoradas": ignoradas,
        "dry_run": dry_run,
    }


def criar_lancamento_crm(
    loja_id: int,
    data: dict,
    vendedor_id: int | None,
    is_owner: bool,
    recorrente: bool = False,
    frequencia: str = "mensal",
    data_fim_recorrencia=None,
):
    """Cria lançamento financeiro ou recorrência no CRM.

    - Se recorrente=True: cria série de recorrência e retorna o primeiro lançamento.
    - Se recorrente=False: cria lançamento avulso com origem MANUAL.

    Args:
        loja_id: ID da loja
        data: dict com os dados validados (sem os campos de recorrência)
        vendedor_id: ID do vendedor logado (None se owner)
        is_owner: True se o usuário é owner da loja
        recorrente: Se deve criar série de recorrência
        frequencia: Frequência da recorrência ('mensal', 'semanal', etc.)
        data_fim_recorrencia: Data final da série (opcional)

    Returns:
        LancamentoFinanceiroCRM: instância criada

    """
    from rest_framework.exceptions import ValidationError

    from .models.financeiro import LancamentoFinanceiroCRM
    from .services_recorrencia_financeiro import criar_recorrencia_com_primeiro_lancamento

    if vendedor_id and not is_owner:
        data["vendedor_id"] = vendedor_id

    if recorrente:
        vendedor = data.get("vendedor") or data.get("vendedor_id")
        vendedor_id_final = getattr(vendedor, "id", vendedor)
        if not vendedor_id_final:
            raise ValidationError({"vendedor": "Vendedor obrigatório para recorrência."})
        _, lanc = criar_recorrencia_com_primeiro_lancamento(
            loja_id,
            vendedor_id=vendedor_id_final,
            tipo=data["tipo"],
            descricao=data["descricao"],
            valor=data["valor"],
            data_vencimento=data["data_vencimento"],
            frequencia=frequencia,
            data_fim=data_fim_recorrencia,
            grupo=data.get("grupo"),
            observacoes=data.get("observacoes") or "",
            status=data.get("status", LancamentoFinanceiroCRM.STATUS_PENDENTE),
            data_pagamento=data.get("data_pagamento"),
        )
        return lanc

    # Lançamento avulso
    extra = {"origem": LancamentoFinanceiroCRM.ORIGEM_MANUAL}
    if vendedor_id and not is_owner:
        extra["vendedor_id"] = vendedor_id
    return LancamentoFinanceiroCRM.objects.create(**data, **extra)
