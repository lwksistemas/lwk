"""Cálculo de comissão do profissional do salão por categoria de serviço."""
from __future__ import annotations

from decimal import Decimal

from .models import CategoriaServico, ProfissionalComissao


def calcular_comissao_agendamento(agendamento, valor_base: Decimal | None = None) -> tuple[Decimal, Decimal]:
    """Retorna (percentual_snapshot, valor_comissao) para o agendamento.

    Match: serviço.categoria (string) ↔ CategoriaServico.nome (case-insensitive)
    + regra ativa ProfissionalComissao do profissional.
    """
    zero = Decimal("0.00")
    base = Decimal(str(valor_base if valor_base is not None else (agendamento.valor or 0)))
    if base < 0:
        base = zero

    profissional_id = getattr(agendamento, "profissional_id", None)
    servico = getattr(agendamento, "servico", None)
    if not profissional_id or not servico:
        return zero, zero

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

    regra = (
        ProfissionalComissao.objects.filter(
            profissional_id=profissional_id,
            categoria_id=categoria.id,
            is_active=True,
        )
        .order_by("-id")
        .first()
    )
    if not regra:
        return zero, zero

    valor_regra = Decimal(str(regra.valor or 0))
    if regra.modo == ProfissionalComissao.MODO_FIXO:
        return zero, max(valor_regra, zero).quantize(Decimal("0.01"))

    # percentual
    pct = max(valor_regra, zero)
    comissao = (base * pct / Decimal("100")).quantize(Decimal("0.01"))
    return pct.quantize(Decimal("0.01")), comissao
