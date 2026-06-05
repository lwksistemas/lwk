"""
Cálculo unificado de comissão profissional (percentual ou valor fixo).
"""
from decimal import Decimal
from typing import Optional, Tuple

from .models import ProfessionalCommission


def calcular_comissao_decimal(
    comissao: Optional[ProfessionalCommission],
    base: Decimal,
) -> Decimal:
    """Percentual sobre a base; valor fixo por atendimento (independente da base)."""
    if not comissao:
        return Decimal('0')
    if comissao.modo == 'fixo':
        return comissao.valor.quantize(Decimal('0.01'))
    if base <= 0:
        return Decimal('0')
    return (base * comissao.valor / Decimal('100')).quantize(Decimal('0.01'))


def calcular_comissao_payment(
    comissao: Optional[ProfessionalCommission],
    valor_pagamento: Decimal,
) -> Tuple[int, Decimal]:
    """
    Para o modelo Payment: retorna (percentual int, valor Decimal).
    Em modo fixo, percentual é 0 e valor é o valor fixo da regra.
    """
    if not comissao:
        return 0, Decimal('0')
    if comissao.modo == 'percentual':
        pct = int(comissao.valor)
        val = (valor_pagamento * comissao.valor / Decimal('100')).quantize(Decimal('0.01'))
        return pct, val
    return 0, comissao.valor
