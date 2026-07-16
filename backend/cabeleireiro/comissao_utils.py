"""Cálculo de comissão do profissional do salão por serviço (e fallback por categoria)."""
from __future__ import annotations

from decimal import Decimal

from .models import CategoriaServico, ProfissionalComissao


def _aplicar_regra(regra: ProfissionalComissao, base: Decimal) -> tuple[Decimal, Decimal]:
    zero = Decimal("0.00")
    valor_regra = Decimal(str(regra.valor or 0))
    if regra.modo == ProfissionalComissao.MODO_FIXO:
        return zero, max(valor_regra, zero).quantize(Decimal("0.01"))
    pct = max(valor_regra, zero)
    comissao = (base * pct / Decimal("100")).quantize(Decimal("0.01"))
    return pct.quantize(Decimal("0.01")), comissao


def calcular_comissao_agendamento(agendamento, valor_base: Decimal | None = None) -> tuple[Decimal, Decimal]:
    """Retorna (percentual_snapshot, valor_comissao) para o agendamento.

    Prioridade:
    1. Regra ativa do profissional + serviço específico
    2. Fallback legado: profissional + categoria (servico nulo)
    """
    zero = Decimal("0.00")
    base = Decimal(str(valor_base if valor_base is not None else (agendamento.valor or 0)))
    if base < 0:
        base = zero

    profissional_id = getattr(agendamento, "profissional_id", None)
    servico = getattr(agendamento, "servico", None)
    if not profissional_id or not servico:
        return zero, zero

    regra = (
        ProfissionalComissao.objects.filter(
            profissional_id=profissional_id,
            servico_id=servico.id,
            is_active=True,
        )
        .order_by("-id")
        .first()
    )
    if regra:
        return _aplicar_regra(regra, base)

    # Fallback legado (só categoria)
    cat_nome = (getattr(servico, "categoria", None) or "").strip()
    if not cat_nome:
        return zero, zero
    categoria = (
        CategoriaServico.objects.filter(is_active=True, nome__iexact=cat_nome)
        .order_by("id")
        .first()
    )
    if not categoria:
        return zero, zero
    regra_cat = (
        ProfissionalComissao.objects.filter(
            profissional_id=profissional_id,
            categoria_id=categoria.id,
            servico__isnull=True,
            is_active=True,
        )
        .order_by("-id")
        .first()
    )
    if not regra_cat:
        return zero, zero
    return _aplicar_regra(regra_cat, base)
