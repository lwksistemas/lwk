"""Desconto do protocolo personalizado no comprovante."""
import logging

logger = logging.getLogger(__name__)
def _dados_protocolo_recibo(appointment) -> dict:
    """Valores do protocolo personalizado, para o cliente ver o desconto no recibo."""
    contrato = getattr(appointment, "protocolo_contrato", None)
    if contrato is None or getattr(contrato, "protocol_id", None):
        return {}
    try:
        bruto = round(float(contrato.valor_bruto or 0), 2)
        liquido = round(float(contrato.valor_total or 0), 2)
    except (TypeError, ValueError):
        return {}
    if bruto <= liquido + 0.009:
        return {}
    precos = []
    try:
        for linha in contrato.procedimentos.select_related("procedure").order_by("id"):
            precos.append({
                "nome": getattr(getattr(linha, "procedure", None), "nome", "") or "",
                "valor": round(float(linha.valor or 0), 2),
            })
    except Exception:
        logger.exception("Erro ao ler procedimentos do protocolo no recibo")
        precos = []
    return {
        "protocolo_valor_sem_desconto": bruto,
        "protocolo_valor_com_desconto": liquido,
        "protocolo_procedimentos": precos,
    }


def _precos_brutos_das_linhas(procs: list[dict], precos: list[dict]) -> list[dict] | None:
    """Troca o valor líquido de cada linha pelo preço do protocolo, quando os nomes batem."""
    if not procs or len(procs) != len(precos):
        return None
    usados: set[int] = set()
    saida = []
    for proc in procs:
        nome = (proc.get("nome") or "").strip().casefold()
        achou = None
        for indice, bruto in enumerate(precos):
            if indice in usados:
                continue
            if (bruto.get("nome") or "").strip().casefold() == nome and nome:
                achou = indice
                break
        if achou is None:
            return None
        usados.add(achou)
        item = dict(proc)
        item["valor"] = round(float(precos[achou].get("valor") or 0), 2)
        saida.append(item)
    soma = round(sum(item["valor"] for item in saida), 2)
    bruto = round(sum(float(item.get("valor") or 0) for item in precos), 2)
    if abs(soma - bruto) > 0.05:
        return None
    return saida


def _escalar_valores_recibo(procs: list[dict], alvo: float) -> list[dict]:
    soma = round(sum(float(p.get("valor") or 0) for p in procs), 2)
    if soma <= 0.009:
        return procs
    restante = round(alvo, 2)
    saida = []
    for indice, proc in enumerate(procs):
        item = dict(proc)
        if indice == len(procs) - 1:
            item["valor"] = round(max(restante, 0.0), 2)
        else:
            parte = round(float(proc.get("valor") or 0) / soma * alvo, 2)
            item["valor"] = parte
            restante = round(restante - parte, 2)
        saida.append(item)
    return saida


def _visita_cobra_pacote(soma: float, liquido: float) -> bool:
    """A visita cobra o pacote quando as linhas somam o valor já com desconto."""
    return abs(soma - liquido) <= 0.05


def _aplicar_desconto_do_protocolo(ctx: dict) -> dict:
    """No pagamento do pacote, as linhas voltam ao preço cheio e o desconto entra na conta.

    Na parcela, o total da visita permanece a parte da sessão. Os dois valores do
    protocolo saem à parte, para a cliente ver.
    """
    bruto = float(ctx.get("protocolo_valor_sem_desconto") or 0)
    liquido = float(ctx.get("protocolo_valor_com_desconto") or 0)
    if bruto <= liquido + 0.009:
        return ctx
    procs = [dict(p) for p in (ctx.get("procedimentos") or [])]
    soma = round(sum(float(p.get("valor") or 0) for p in procs), 2)
    valor_visita = float(ctx.get("valor_total") or 0)
    if soma <= 0.009 and valor_visita <= 0.009:
        return ctx
    ctx = dict(ctx)
    if _visita_cobra_pacote(soma, liquido) and soma > 0.009:
        ajustados = _precos_brutos_das_linhas(procs, ctx.get("protocolo_procedimentos") or [])
        if ajustados is None:
            ajustados = _escalar_valores_recibo(procs, bruto)
        taxa_parte = round(float(ctx.get("subtotal") or 0) - soma, 2)
        ctx["procedimentos"] = ajustados
        ctx["subtotal"] = round(bruto + max(taxa_parte, 0.0), 2)
        ctx["desconto_protocolo"] = round(bruto - liquido, 2)
        ctx.pop("protocolo_valores_informativos", None)
        return ctx
    ctx["protocolo_valores_informativos"] = True
    return ctx
