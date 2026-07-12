"""
Cálculo unificado de comissão profissional (percentual ou valor fixo).
"""
from decimal import Decimal
from typing import Optional

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


