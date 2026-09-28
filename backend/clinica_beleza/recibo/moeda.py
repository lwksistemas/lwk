"""Formatação de valores do recibo no padrão brasileiro."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def formatar_moeda_recibo(valor) -> str:
    """R$ 1.272,67 — milhar com ponto e centavos com vírgula."""
    try:
        quant = Decimal(str(valor if valor is not None else 0)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, ValueError, TypeError):
        quant = Decimal("0.00")
    negativo = quant < 0
    texto = f"{abs(quant):.2f}"
    inteiro, frac = texto.split(".")
    partes: list[str] = []
    while inteiro:
        partes.append(inteiro[-3:])
        inteiro = inteiro[:-3]
    corpo = ".".join(reversed(partes))
    sinal = "-" if negativo else ""
    return f"{sinal}R$ {corpo},{frac}"
