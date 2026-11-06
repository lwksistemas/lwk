"""Fecha a conta impressa: descontos, abatimento e protocolo."""
from .itens_recibo import _omitir_taxa_junto_do_procedimento, aplicar_valor_consulta_do_local
from .nomes_recibo import nome_exibicao_procedimento_recibo
from .protocolo_recibo import _aplicar_desconto_do_protocolo
def saldo_aberto_recibo(ctx: dict) -> float:
    valor_pago = float(ctx.get("valor_pago") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    try:
        saldo = float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)))
    except (TypeError, ValueError):
        saldo = max(valor_total - valor_pago, 0.0)
    return saldo if saldo > 0.009 else 0.0


def _descontos_conhecidos_recibo(ctx: dict) -> tuple[float, float]:
    if ctx.get("ocultar_desconto_retorno"):
        return 0.0, float(ctx.get("desconto") or 0)
    desconto_retorno = float(ctx.get("desconto_retorno") or 0)
    if desconto_retorno <= 0 and ctx.get("retorno_gratuito"):
        cobrada = float(ctx.get("taxa_consulta") or 0)
        desconto_retorno = cobrada if cobrada > 0.009 else float(ctx.get("taxa_consulta_referencia") or 0)
    desconto = float(ctx.get("desconto") or 0)
    return desconto_retorno, desconto


def _alinhar_total_com_desconto_da_consulta(ctx: dict) -> dict:
    """Se o total ainda inclui a consulta lançada, o desconto sai desse total."""
    desconto = float(ctx.get("desconto_retorno") or 0)
    if desconto <= 0.009:
        return ctx
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    if abs(subtotal - valor_total) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["valor_total"] = round(max(0.0, valor_total - desconto), 2)
    pago = float(ctx.get("valor_pago") or 0)
    ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
    return ctx


def _ocultar_taxa_impressa_no_retorno(ctx: dict) -> dict:
    """Consulta lançada e descontada permanece na conta.

    Consulta que não foi lançada não ganha linha nem frase de desconto.
    O total já fechado permanece.
    """
    if not ctx.get("retorno_gratuito"):
        return ctx
    taxa_cobrada = float(ctx.get("taxa_consulta") or 0)
    if taxa_cobrada > 0.009:
        ctx = dict(ctx)
        if float(ctx.get("desconto_retorno") or 0) <= 0.009:
            ctx["desconto_retorno"] = taxa_cobrada
        return _alinhar_total_com_desconto_da_consulta(ctx)
    ref = float(ctx.get("taxa_consulta_referencia") or 0)
    if ref <= 0.009:
        ref = float(ctx.get("desconto_retorno") or 0)
    ctx = dict(ctx)
    if ref > 0.009:
        ctx["subtotal"] = round(max(0.0, float(ctx.get("subtotal") or 0) - ref), 2)
    ctx["desconto_retorno"] = 0
    ctx["taxa_consulta"] = 0
    ctx["ocultar_desconto_retorno"] = True
    return ctx


def _rotulo_abatimento(procedimentos, gap: float) -> str:
    iguais = []
    for proc in procedimentos or []:
        try:
            valor = float(proc.get("valor") or 0)
        except (TypeError, ValueError):
            continue
        if abs(valor - gap) <= 0.02 and (proc.get("nome") or "").strip():
            iguais.append((proc.get("nome") or "").strip())
    if len(iguais) == 1:
        return f"Abatimento — {nome_exibicao_procedimento_recibo(iguais[0])}"
    return "Abatimento"


def recebido_a_maior_recibo(ctx: dict) -> float:
    """Dinheiro recebido acima do total cobrado, sem troco lançado."""
    total = float(ctx.get("valor_total") or 0)
    pago = float(ctx.get("valor_pago") or 0)
    extra = round(pago - total, 2)
    return extra if extra > 0.009 else 0.0


def _repor_preco_que_fecha_conta(ctx: dict) -> dict:
    """Linha gravada a R$ 0 cujo preço de cadastro fecha a conta com o total cobrado."""
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    falta = round(valor_total - (subtotal - desconto_retorno - desconto), 2)
    if falta <= 0.009:
        return ctx
    procs = [dict(p) for p in (ctx.get("procedimentos") or [])]
    candidatos = []
    for proc in procs:
        valor = float(proc.get("valor") or 0)
        catalogo = float(proc.get("preco_cadastro") or 0)
        if valor <= 0.009 and abs(catalogo - falta) <= 0.02:
            candidatos.append(proc)
    if len(candidatos) != 1:
        return ctx
    candidatos[0]["valor"] = round(falta, 2)
    ctx["procedimentos"] = procs
    ctx["subtotal"] = round(subtotal + falta, 2)
    return ctx


def _desconto_comercial_sai_do_total(ctx: dict) -> dict:
    """Procedimento 1.500 e desconto 500 deixam saldo 1.000.

    Só reduz quando o total gravado ainda é o preço antes do desconto comercial.
    Se o pagamento já guardou o líquido, o total permanece.
    """
    _desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto <= 0.009:
        return ctx
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    sem_comercial = round(subtotal - _desconto_retorno, 2)
    if abs(sem_comercial - valor_total) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["valor_total"] = round(max(0.0, valor_total - desconto), 2)
    pago = float(ctx.get("valor_pago") or 0)
    ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
    return ctx


def _incorporar_desconto_da_linha_do_produto(ctx: dict) -> dict:
    """O desconto do produto sai na linha Desconto e o subtotal fica no preço cheio.

    A prévia aprovada mostra o item a R$ 300, o subtotal a R$ 300, o desconto de
    R$ 35 e o total pago a R$ 265.
    """
    bruto = 0.0
    desconto_linhas = 0.0
    for item in ctx.get("produtos") or []:
        try:
            quantidade = float(str(item.get("quantidade") or 0).replace(",", "."))
            preco = float(item.get("preco_unitario") or 0)
            desconto_item = float(item.get("desconto") or 0)
        except (TypeError, ValueError):
            continue
        if quantidade <= 0:
            continue
        bruto += quantidade * preco
        desconto_linhas += desconto_item
    bruto = round(bruto, 2)
    desconto_linhas = round(desconto_linhas, 2)
    if desconto_linhas <= 0.009 or bruto <= 0.009:
        return ctx
    desconto = round(float(ctx.get("desconto") or 0), 2)
    subtotal = round(float(ctx.get("subtotal") or 0), 2)
    if desconto + 0.02 >= desconto_linhas and subtotal + 0.05 >= bruto:
        return ctx
    # A venda de produto grava o subtotal líquido. O recibo mostra o preço cheio
    # e a linha Desconto. Não mexe quando o desconto do pagamento é outro valor.
    preco_cheio = subtotal + 0.05 < bruto and abs((subtotal + desconto_linhas) - bruto) <= 0.05
    if not preco_cheio:
        return ctx
    if desconto > 0.009 and abs(desconto - desconto_linhas) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["subtotal"] = round(bruto, 2)
    if desconto <= 0.009:
        ctx["desconto"] = desconto_linhas
    return ctx


def reconciliar_conta_recibo(ctx: dict) -> dict:
    """Fecha a conta impressa: taxa omitida entra no total; o resto vira abatimento.

    O desconto comercial sai do total quando ainda estava somado no valor cobrado.
    Se a soma dos itens menos os descontos conhecidos for maior, a diferença sai
    como linha própria (ex.: procedimento não cobrado).
    Linha a R$ 0 cujo preço de cadastro explica o total cobrado volta a esse preço.
    O desconto do protocolo personalizado entra como linha quando a visita cobra o pacote.
    """
    ctx = _incorporar_desconto_da_linha_do_produto(ctx)
    ctx = _aplicar_desconto_do_protocolo(
        _desconto_comercial_sai_do_total(
            _repor_preco_que_fecha_conta(aplicar_valor_consulta_do_local(dict(ctx)))
        )
    )
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    desconto_protocolo = float(ctx.get("desconto_protocolo") or 0)
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    gap = round(subtotal - desconto_retorno - desconto - desconto_protocolo - valor_total, 2)
    ctx.pop("abatimento", None)
    ctx.pop("abatimento_label", None)
    if gap <= 0.009:
        return _ocultar_taxa_impressa_no_retorno(ctx)
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0.009:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    omitir_taxa = _omitir_taxa_junto_do_procedimento(ctx)
    if (
        not omitir_taxa
        and not ctx.get("retorno_gratuito")
        and taxa > 0.009
        and abs(gap - taxa) <= 0.02
    ):
        ctx["valor_total"] = round(valor_total + gap, 2)
        pago = float(ctx.get("valor_pago") or 0)
        ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
        return _ocultar_taxa_impressa_no_retorno(ctx)
    ctx["abatimento"] = gap
    ctx["abatimento_label"] = _rotulo_abatimento(ctx.get("procedimentos"), gap)
    return _ocultar_taxa_impressa_no_retorno(ctx)

def resumo_financeiro_recibo(ctx: dict) -> str:
    """Mantido por compatibilidade. O saldo já aparece na linha própria."""
    return ""


def _outro_desconto_na_conta(ctx: dict) -> bool:
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto_retorno > 0.009 or desconto > 0.009:
        return True
    return float(ctx.get("abatimento") or 0) > 0.009


def rotulo_subtotal_recibo(ctx: dict) -> str:
    if float(ctx.get("desconto_protocolo") or 0) > 0.009:
        return "Valor sem desconto"
    return "Subtotal"


def rotulo_total_recibo(ctx: dict) -> str:
    if float(ctx.get("desconto_protocolo") or 0) > 0.009 and not _outro_desconto_na_conta(ctx):
        return "Valor com desconto"
    return "Total"


def linha_valor_com_desconto_recibo(ctx: dict) -> tuple[str, float] | None:
    """Quando ainda há outro desconto, o líquido do protocolo sai numa linha própria."""
    if float(ctx.get("desconto_protocolo") or 0) <= 0.009 or not _outro_desconto_na_conta(ctx):
        return None
    return ("Valor com desconto", float(ctx.get("protocolo_valor_com_desconto") or 0))


def linhas_protocolo_informativo(ctx: dict) -> list[tuple[str, float]]:
    """Parcela da sessão: os dois valores do protocolo, sem alterar o total da visita."""
    if not ctx.get("protocolo_valores_informativos"):
        return []
    bruto = float(ctx.get("protocolo_valor_sem_desconto") or 0)
    liquido = float(ctx.get("protocolo_valor_com_desconto") or 0)
    if bruto <= liquido + 0.009:
        return []
    return [
        ("Valor sem desconto", bruto),
        ("Valor com desconto", liquido),
    ]


def _linhas_descontos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linhas de desconto (retorno gratuito, protocolo, desconto comercial e abatimento)."""
    linhas: list[tuple[str, float]] = []
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto_retorno > 0:
        linhas.append(("Desconto da avaliação", desconto_retorno))
    desconto_protocolo = float(ctx.get("desconto_protocolo") or 0)
    if desconto_protocolo > 0.009:
        linhas.append(("Desconto do protocolo", desconto_protocolo))
    if desconto > 0:
        linhas.append(("Desconto", desconto))
    abatimento = float(ctx.get("abatimento") or 0)
    if abatimento > 0.009:
        linhas.append((ctx.get("abatimento_label") or "Abatimento", abatimento))
    return linhas
