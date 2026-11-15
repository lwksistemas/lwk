"""Recebimento do salão. A comissão usa o percentual gravado no profissional na hora do caixa."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .models import FORMAS_PAGAMENTO

ROTULOS = dict(FORMAS_PAGAMENTO)

CENTAVO = Decimal("0.01")
FORMAS = {codigo for codigo, _ in FORMAS_PAGAMENTO}


def quantia(valor) -> Decimal:
    texto = str(0 if valor in (None, "") else valor).strip().replace(",", ".")
    try:
        numero = Decimal(texto)
    except InvalidOperation as exc:
        raise ValueError("Informe o desconto em reais.") from exc
    return numero.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def interpretar_formas(dados, valor_liquido: Decimal) -> list[dict]:
    """Partes que somam o valor líquido. Lista vazia quando o desconto quita o atendimento."""
    valor_liquido = quantia(valor_liquido)
    brutas = dados.get("formas") if isinstance(dados, dict) else None
    if isinstance(brutas, list):
        if not brutas:
            if valor_liquido == 0:
                return []
            raise ValueError("Adicione ao menos uma forma de pagamento.")
        partes = []
        for item in brutas:
            if not isinstance(item, dict):
                raise ValueError("Escolha dinheiro, Pix, débito ou crédito.")
            forma = str(item.get("forma") or "").strip()
            if forma not in FORMAS:
                raise ValueError("Escolha dinheiro, Pix, débito ou crédito.")
            parte = quantia(item.get("valor"))
            if parte <= 0:
                raise ValueError("Informe o valor de cada forma de pagamento.")
            partes.append({"forma": forma, "valor": f"{parte:.2f}"})
        soma = sum((quantia(item["valor"]) for item in partes), Decimal("0"))
        if soma != valor_liquido:
            raise ValueError(f"A soma das formas precisa fechar R$ {valor_liquido:.2f}.")
        return partes
    if valor_liquido == 0:
        return []
    forma = str((dados.get("forma") if isinstance(dados, dict) else "") or "").strip()
    if forma not in FORMAS:
        raise ValueError("Escolha dinheiro, Pix, débito ou crédito.")
    return [{"forma": forma, "valor": f"{valor_liquido:.2f}"}]


def rotulo_formas(partes, forma_unica: str) -> str:
    if not partes or len(partes) == 1:
        return ROTULOS.get(forma_unica, forma_unica)
    return " e ".join(ROTULOS.get(item.get("forma"), item.get("forma", "")) for item in partes)


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
