"""Formatação numérica/textual comum a documentos fiscais."""
import re
from decimal import ROUND_HALF_UP, Decimal


def digitos(valor, tamanho: int = 0) -> str:
    texto = re.sub(r"\D", "", str(valor or ""))
    if tamanho:
        return texto.zfill(tamanho)[-tamanho:]
    return texto


def dinheiro(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
