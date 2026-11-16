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


def motivo_bloqueio_recebimento(local: str, origem: str, papel: str) -> str | None:
    """Um atendimento quitado não é cobrado de novo. O lugar do recebimento é o da configuração."""
    if origem == "agenda" and local == "caixa":
        return "O recebimento deste salão fica no Caixa/PDV."
    if origem == "caixa" and local == "agenda":
        return "O recebimento deste salão fica na agenda."
    if papel == "profissional" and local == "caixa":
        return "Neste salão, o profissional não recebe. O pagamento fica no caixa."
    if papel == "recepcionista" and origem != "caixa":
        return "A recepção recebe no Caixa/PDV."
    return None


def rotulo_formas(partes, forma_unica: str) -> str:
    if not partes or len(partes) == 1:
        return ROTULOS.get(forma_unica, forma_unica)
    return " e ".join(ROTULOS.get(item.get("forma"), item.get("forma", "")) for item in partes)


def calcular_recebimento(preco, desconto, percentual, *, tipo="percentual", fixo=Decimal("0")) -> tuple[Decimal, Decimal]:
    preco = quantia(preco)
    desconto = quantia(desconto)
    percentual = quantia(percentual)
    fixo = quantia(fixo)
    if desconto < 0 or desconto > preco:
        raise ValueError("O desconto não pode passar do valor do serviço.")
    if percentual < 0 or fixo < 0:
        raise ValueError("A comissão do profissional não pode ser negativa.")
    if tipo == "percentual" and percentual > 100:
        raise ValueError("A porcentagem da comissão não pode passar de 100.")
    valor = (preco - desconto).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    if tipo == "fixo":
        return valor, min(fixo, valor)
    comissao = (valor * percentual / Decimal("100")).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return valor, comissao


def regra_da_comissao(profissional, servico_id):
    """O procedimento escolhido pelo administrador vale mais que a comissão padrão."""
    from .models import ComissaoProcedimento

    regra = ComissaoProcedimento.objects.filter(profissional=profissional, servico_id=servico_id).first()
    if regra is not None:
        return regra.tipo, regra.valor
    tipo = getattr(profissional, "comissao_tipo", "") or "percentual"
    if tipo == "fixo":
        return "fixo", profissional.comissao_fixa
    return "percentual", profissional.comissao_percentual


def gravar_comissoes(profissional, itens) -> None:
    """Grava só o procedimento que o administrador definiu. Lista vazia apaga as regras."""
    from .models import ComissaoProcedimento, Servico

    if itens is None:
        return
    if not isinstance(itens, list):
        raise ValueError("Informe a comissão de cada procedimento.")
    mantidos = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        tipo = (item.get("tipo") or "percentual").strip()
        if tipo not in {"percentual", "fixo"}:
            raise ValueError("Escolha porcentagem ou valor fixo em cada procedimento.")
        valor = quantia(item.get("valor") or 0)
        if valor < 0 or (tipo == "percentual" and valor > 100):
            raise ValueError("A porcentagem fica entre 0 e 100. O valor fixo não pode ser negativo.")
        servico = Servico.objects.filter(pk=item.get("servico"), is_active=True).first()
        if servico is None:
            continue
        regra, _criada = ComissaoProcedimento.objects.update_or_create(
            profissional=profissional,
            servico=servico,
            defaults={"tipo": tipo, "valor": valor},
        )
        mantidos.append(regra.id)
    ComissaoProcedimento.objects.filter(profissional=profissional).exclude(id__in=mantidos).delete()


def comissao_do_atendimento(profissional, servico_id, preco, desconto) -> tuple[Decimal, Decimal, Decimal]:
    tipo, base = regra_da_comissao(profissional, servico_id)
    if tipo == "fixo":
        valor, comissao = calcular_recebimento(preco, desconto, 0, tipo="fixo", fixo=base)
        return valor, comissao, Decimal("0")
    valor, comissao = calcular_recebimento(preco, desconto, base)
    return valor, comissao, quantia(base)
