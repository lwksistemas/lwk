"""Recebimento do salão. A comissão usa o percentual gravado no profissional na hora do caixa."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .models import FORMAS_PAGAMENTO

CENTAVO = Decimal("0.01")
FORMAS = {codigo for codigo, _ in FORMAS_PAGAMENTO}


def quantia(valor) -> Decimal:
    texto = str(0 if valor in (None, "") else valor).strip().replace(",", ".")
    try:
        numero = Decimal(texto)
    except InvalidOperation as exc:
        raise ValueError("Informe o desconto em reais.") from exc
    return numero.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_recebimento(preco, desconto, percentual) -> tuple[Decimal, Decimal]:
    preco = quantia(preco)
    desconto = quantia(desconto)
    percentual = quantia(percentual)
    if desconto < 0 or desconto > preco:
        raise ValueError("O desconto não pode passar do valor do serviço.")
    if percentual < 0:
        raise ValueError("A comissão do profissional não pode ser negativa.")
    valor = (preco - desconto).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    comissao = (valor * percentual / Decimal("100")).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return valor, comissao
