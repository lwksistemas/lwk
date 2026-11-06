"""Procedimentos, taxa de avaliação, convênio e produtos do comprovante."""
import logging

from .nomes_recibo import nome_exibicao_procedimento_recibo

logger = logging.getLogger(__name__)
def _buscar_procedimentos_recibo(appointment) -> list[dict]:
    procs = []
    try:
        ap_procs = appointment.appointment_procedures.select_related("procedure").all()
        for ap in ap_procs:
            procs.append({
                "nome": ap.procedure.nome,
                "valor": float(ap.get_valor()),
                "preco_cadastro": float(getattr(ap.procedure, "preco", 0) or 0),
            })
    except Exception:
        logger.exception("Erro ao listar procedimentos do recibo")
    if not procs and appointment.procedure:
        nome_legado = getattr(appointment.procedure, "nome", "") or ""
        if isinstance(nome_legado, str) and nome_legado.strip() and nome_legado.strip().casefold() != "consulta":
            procs = [{"nome": nome_legado.strip(), "valor": float(appointment.procedure.preco or 0)}]
    procs = _anexar_procedimento_do_retorno(appointment, procs)
    if not procs:
        procs.append({"nome": "Consulta", "valor": 0.0})
    return procs


def _anexar_procedimento_do_retorno(appointment, procs: list[dict]) -> list[dict]:
    """Retorno sem valor ainda precisa citar o procedimento realizado."""
    nomes = {
        (p.get("nome") or "").strip().casefold()
        for p in procs
        if isinstance(p.get("nome"), str)
    }
    retorno = getattr(appointment, "retorno_procedure", None)
    nome_retorno = getattr(retorno, "nome", None)
    if isinstance(nome_retorno, str) and nome_retorno.strip() and nome_retorno.strip().casefold() not in nomes:
        procs.append({"nome": nome_retorno.strip(), "valor": 0.0})
        return procs
    if procs:
        return procs
    consulta = getattr(appointment, "consulta", None)
    if consulta is None or not getattr(consulta, "pk", None):
        return procs
    try:
        from django.db.models import Model

        if not isinstance(consulta, Model):
            return procs
        evo = consulta.evolucoes.order_by("-created_at").first()
    except Exception:
        logger.exception("Erro ao ler procedimento realizado do retorno")
        return procs
    texto = getattr(evo, "procedimento_realizado", "") if evo else ""
    if isinstance(texto, str) and texto.strip():
        procs.append({"nome": texto.strip(), "valor": 0.0})
    return procs


def _calcular_taxa_retorno_recibo(appointment, loja_id):
    taxa_consulta = 0.0
    taxa_consulta_referencia = 0.0
    retorno_gratuito = False
    retorno_dias = None
    retorno_aviso = ""
    try:
        consulta = getattr(appointment, "consulta", None)
        if consulta:
            taxa_consulta = float(getattr(consulta, "valor_consulta", 0) or 0)
        from .retorno_info import montar_info_retorno_recibo

        info_ret = montar_info_retorno_recibo(consulta, appointment, loja_id=loja_id)
        retorno_gratuito = bool(info_ret.get("retorno_gratuito"))
        taxa_consulta_referencia = float(info_ret.get("taxa_consulta_referencia") or 0)
        retorno_dias = info_ret.get("retorno_dias")
        retorno_aviso = (info_ret.get("retorno_aviso") or "").strip()
        if retorno_gratuito and taxa_consulta_referencia <= 0 and taxa_consulta > 0:
            taxa_consulta_referencia = taxa_consulta
    except Exception:
        logger.exception("Erro ao ler taxa de consulta do recibo")
    from clinica_beleza.retorno_service import cobrar_taxa_com_procedimento

    return {
        "taxa_consulta": taxa_consulta,
        "taxa_consulta_referencia": taxa_consulta_referencia,
        "retorno_gratuito": retorno_gratuito,
        "retorno_dias": retorno_dias,
        "retorno_aviso": retorno_aviso,
        "cobrar_taxa_com_procedimento": cobrar_taxa_com_procedimento(loja_id),
    }


def _calcular_subtotal_recibo(taxa_info, procs, valor_total, desconto):
    taxa_consulta = taxa_info["taxa_consulta"]
    taxa_consulta_referencia = taxa_info["taxa_consulta_referencia"]
    retorno_gratuito = taxa_info["retorno_gratuito"]
    desconto_retorno = (
        float(taxa_consulta_referencia)
        if retorno_gratuito and taxa_consulta_referencia > 0
        else 0.0
    )
    taxa_para_subtotal = (
        taxa_consulta_referencia if retorno_gratuito and taxa_consulta_referencia > 0 else taxa_consulta
    )
    servicos_soma = taxa_para_subtotal + sum(p["valor"] for p in procs)
    if desconto_retorno > 0 or desconto > 0:
        subtotal = servicos_soma
    else:
        subtotal = servicos_soma if servicos_soma > 0 else valor_total
    return subtotal, desconto_retorno

def recibo_so_consulta(ctx: dict) -> bool:
    """Atendimento sem procedimento cobrado: o recibo precisa citar a consulta."""
    for p in ctx.get("procedimentos") or []:
        if float(p.get("valor") or 0) > 0.009:
            return False
        nome = (p.get("nome") or "").strip().casefold()
        if nome and nome not in ("consulta", "taxa de consulta", "taxa de avaliação"):
            return False
    return True


def _nome_cadastro(obj) -> str:
    nome = getattr(obj, "nome", "") if obj is not None else ""
    return nome.strip() if isinstance(nome, str) else ""


def _local_convenio_recibo(appointment) -> dict:
    consulta = getattr(appointment, "consulta", None)
    local = getattr(consulta, "local_atendimento", None) if consulta is not None else None
    if local is None:
        local = getattr(appointment, "local_atendimento", None)
    convenio = getattr(consulta, "convenio", None) if consulta is not None else None
    if convenio is None:
        convenio = getattr(appointment, "convenio", None)
    return {
        "local_nome": _nome_cadastro(local),
        "convenio_nome": _nome_cadastro(convenio) or "Particular",
    }


def linhas_local_convenio_recibo(ctx: dict) -> list[tuple[str, str]]:
    """Convênio só no recibo de consulta, sem outro procedimento. O local não entra no cupom."""
    if not recibo_so_consulta(ctx):
        return []
    convenio = (ctx.get("convenio_nome") or "").strip()
    if isinstance(convenio, str) and convenio:
        return [("Convênio", convenio)]
    return []


def _omitir_taxa_junto_do_procedimento(ctx: dict) -> bool:
    """Clínica desligou a taxa e o atendimento tem procedimento além da consulta.

    Taxa já gravada na consulta continua no recibo (atendimento antigo).
    """
    if ctx.get("cobrar_taxa_com_procedimento") is not False:
        return False
    if float(ctx.get("taxa_consulta") or 0) > 0.009:
        return False
    return not recibo_so_consulta(ctx)


def aplicar_valor_consulta_do_local(ctx: dict) -> dict:
    """Usa a taxa do local quando a consulta ficou zerada (com ou sem procedimento).

    Fora do retorno gratuito a taxa entra no recibo sempre; no retorno a linha
    e o desconto vêm de taxa_consulta_referencia / desconto_retorno.
    Com a opção desligada, procedimento sem taxa gravada não recebe a taxa.
    """
    if ctx.get("retorno_gratuito") or _omitir_taxa_junto_do_procedimento(ctx):
        return ctx
    if float(ctx.get("taxa_consulta") or 0) > 0.009:
        return ctx
    ref = float(ctx.get("taxa_consulta_referencia") or 0)
    if ref <= 0.009:
        return ctx
    ctx = dict(ctx)
    ctx["taxa_consulta"] = ref
    procs_soma = sum(float(p.get("valor") or 0) for p in (ctx.get("procedimentos") or []))
    ctx["subtotal"] = ref + procs_soma
    if float(ctx.get("valor_total") or 0) <= 0.009:
        ctx["valor_total"] = ctx["subtotal"]
        pago = float(ctx.get("valor_pago") or 0)
        ctx["saldo_devedor"] = max(ctx["valor_total"] - pago, 0.0)
    return ctx


def _linhas_taxa_consulta_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linha da taxa cobrada.

    No retorno, a taxa só entra se foi lançada na consulta. Aí o desconto
    aparece na conta. Taxa que não foi lançada não vira linha nem desconto.
    """
    if _omitir_taxa_junto_do_procedimento(ctx):
        return []
    if ctx.get("retorno_gratuito"):
        taxa = float(ctx.get("taxa_consulta") or 0)
        if taxa > 0.009 and not ctx.get("ocultar_desconto_retorno"):
            return [("Taxa de avaliação", taxa)]
        return []
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    if taxa > 0:
        return [("Taxa de avaliação", taxa)]
    return []


def procedimentos_exibidos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Procedimentos do cupom, com a dose junto do nome e sem consulta zerada repetida."""
    taxa_exibida = 0.0
    linhas_taxa = _linhas_taxa_consulta_recibo(ctx)
    if linhas_taxa:
        taxa_exibida = float(linhas_taxa[0][1] or 0)
    linhas: list[tuple[str, float]] = []
    for proc in ctx.get("procedimentos") or []:
        nome = nome_exibicao_procedimento_recibo(proc.get("nome") or "")
        try:
            valor = float(proc.get("valor") or 0)
        except (TypeError, ValueError):
            valor = 0.0
        if taxa_exibida > 0.009 and valor == 0.0 and nome.casefold() in (
            "consulta", "taxa de consulta", "taxa de avaliação",
        ):
            continue
        linhas.append((nome, valor))
    return linhas


def produtos_exibidos_recibo(ctx: dict) -> list[dict]:
    """Linhas de produto vendido. Insumo de procedimento não entra."""
    linhas = []
    for item in ctx.get("produtos") or []:
        try:
            subtotal = float(item.get("subtotal") or 0)
        except (TypeError, ValueError):
            subtotal = 0.0
        linhas.append({
            "nome": nome_exibicao_procedimento_recibo(item.get("nome") or "Produto"),
            "quantidade": item.get("quantidade") or "0",
            "preco_unitario": float(item.get("preco_unitario") or 0),
            "desconto": float(item.get("desconto") or 0),
            "subtotal": subtotal,
        })
    return linhas
