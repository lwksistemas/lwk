"""Formas de pagamento, custeio da clínica e vencimento."""
import logging
import re

from .moeda import formatar_moeda_recibo

logger = logging.getLogger(__name__)
_ROTULO_DESPESA_RECIBO = "Despesa (clínica)"
_ROTULO_CUSTEIO_RECIBO = "Custeado pela clínica"


def forma_e_custeio_clinica(metodo: str) -> bool:
    """A forma interna DESPESA, com ou sem a data entre parênteses."""
    texto = (metodo or "").strip()
    return (
        texto == _ROTULO_DESPESA_RECIBO
        or texto.startswith(_ROTULO_DESPESA_RECIBO + " ")
        or texto.startswith(_ROTULO_DESPESA_RECIBO + "(")
    )


def rotulo_forma_recibo(metodo: str) -> str:
    """No papel do paciente, custeio da clínica não aparece como forma de pagamento."""
    texto = (metodo or "").strip()
    if not forma_e_custeio_clinica(texto):
        return texto
    return _ROTULO_CUSTEIO_RECIBO + texto[len(_ROTULO_DESPESA_RECIBO):]


def custeado_pela_clinica(ctx: dict) -> bool:
    """True quando todo o valor lançado foi custeado pela clínica."""
    formas = [
        f for f in (ctx.get("formas_pagamento") or [])
        if float(f.get("valor") or 0) > 0.009
    ]
    if formas:
        return all(forma_e_custeio_clinica(str(f.get("metodo") or "")) for f in formas)
    if float(ctx.get("valor_pago") or 0) <= 0.009:
        return False
    return forma_e_custeio_clinica(str(ctx.get("metodo") or ""))


def linha_vencimento_recibo(ctx: dict) -> str:
    """Vencido quando a data já passou na emissão. Sem data, não inventa uma."""
    vencimento = (ctx.get("vencimento") or "").strip()
    if not vencimento:
        return "Sem vencimento"
    data_venc = _data_texto_recibo(vencimento)
    data_emissao = _data_texto_recibo(ctx.get("data_emissao") or ctx.get("data") or "")
    if data_venc and data_emissao and data_venc < data_emissao:
        return f"Vencido em: {vencimento}"
    return f"Vencimento: {vencimento}"


def _data_texto_recibo(texto: str):
    achado = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto or "")
    if not achado:
        return None
    from datetime import date

    try:
        return date(int(achado.group(3)), int(achado.group(2)), int(achado.group(1)))
    except ValueError:
        return None


_DATA_NA_FORMA = re.compile(r"^(?P<forma>.*?)\s*\((?P<data>\d{2}/\d{2}/\d{4})\)\s*$")


def formas_detalhadas_recibo(ctx: dict) -> list[dict]:
    """Cada recebimento já gravado, com data, forma e valor separados."""
    linhas = []
    for item in ctx.get("formas_pagamento") or []:
        try:
            valor = float(item.get("valor") or 0)
        except (TypeError, ValueError):
            continue
        if valor <= 0.009:
            continue
        metodo = str(item.get("metodo") or "").strip()
        if forma_e_custeio_clinica(metodo):
            continue
        forma = str(item.get("forma") or "").strip()
        data = str(item.get("data") or "").strip()
        if not forma or not data:
            achado = _DATA_NA_FORMA.match(metodo)
            if achado:
                forma = forma or achado.group("forma").strip()
                data = data or achado.group("data")
            else:
                forma = forma or metodo
        linhas.append({
            "data": data,
            "forma": rotulo_forma_recibo(forma),
            "valor": round(valor, 2),
        })
    return linhas


def _formas_pagamento_texto(ctx: dict) -> str:
    """Formata formas de pagamento para texto (WhatsApp/email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        if float(ctx.get("valor_pago") or 0) <= 0.009:
            condicao = (ctx.get("condicao_cobranca") or "").strip()
            if condicao:
                return f"  Condição de cobrança: {condicao}\n"
            return ""
        metodo = rotulo_forma_recibo(ctx.get("metodo", ""))
        return f"  {metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}\n"
    lines = [
        f'  • {rotulo_forma_recibo(f["metodo"])} — {formatar_moeda_recibo(f["valor"])}'
        for f in formas
    ]
    return "\n".join(lines) + "\n"


def _formas_pagamento_html(ctx: dict) -> str:
    """Formata formas de pagamento para HTML (corpo do email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = rotulo_forma_recibo(ctx.get("metodo", ""))
        return f"<li>{metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}</li>"
    return "".join(
        f'<li>{rotulo_forma_recibo(f["metodo"])} — {formatar_moeda_recibo(f["valor"])}</li>'
        for f in formas
    )


def _listar_formas_pagamento(payment) -> list[dict]:
    """Retorna formas de pagamento do recibo.

    Agrupa por forma + data do pagamento (mesma forma no mesmo dia soma numa linha).
    Sempre exibe a data em que o cliente pagou cada forma — não confundir com a data
    de emissão do recibo.
    """
    from collections import OrderedDict

    METODOS = dict(payment.PAYMENT_METHOD_CHOICES)
    try:
        parcelas = list(
            payment.parcelas.filter(status="PAID").order_by("payment_date", "id"),
        )
        if parcelas:
            grupos: OrderedDict[tuple[str, str], dict] = OrderedDict()
            for p in parcelas:
                data = getattr(p, "payment_date", None)
                data_key = data.isoformat() if hasattr(data, "isoformat") else str(data or "")
                key = (str(p.payment_method or ""), data_key)
                if key not in grupos:
                    grupos[key] = {
                        "metodo_code": p.payment_method,
                        "data": data,
                        "valor": 0.0,
                    }
                grupos[key]["valor"] += float(p.valor or 0)

            datas = {g["data"] for g in grupos.values() if g["data"]}
            del datas  # mantido por compatibilidade histórica
            result = []
            for g in grupos.values():
                label = METODOS.get(g["metodo_code"], g["metodo_code"])
                # Sempre mostra a data do pagamento (não confundir com a emissão do recibo).
                if g["data"] is not None and hasattr(g["data"], "strftime"):
                    label = f"{label} ({g['data'].strftime('%d/%m/%Y')})"
                valor = round(g["valor"], 2)
                if valor <= 0.009:
                    continue
                result.append({
                    "metodo": label,
                    "forma": METODOS.get(g["metodo_code"], g["metodo_code"]),
                    "data": g["data"].strftime("%d/%m/%Y") if hasattr(g["data"], "strftime") else "",
                    "valor": valor,
                })
            return result
    except Exception:
        logger.exception("Erro ao listar parcelas do recibo (payment %s)", payment.id)
    # A prazo, ou método gravado com valor zero, não é forma de pagamento.
    if payment.payment_method == "PRAZO" or float(payment.amount or 0) <= 0.009:
        return []
    metodo_label = METODOS.get(payment.payment_method, payment.payment_method)
    return [{"metodo": metodo_label, "valor": float(payment.amount or 0)}]
