from datetime import date

from .constants import LABEL_CONSULTA


def _fmt_brl(valor) -> str:
    v = float(valor or 0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_data_br(d: date | None) -> str:
    if not d:
        return "—"
    return d.strftime("%d/%m/%Y")


def _is_linha_consulta(d: dict) -> bool:
    return d.get("tipo_linha") == "consulta" or d.get("procedimento_nome") == LABEL_CONSULTA


def _codigo_pagamento_pdf(forma: str) -> str:
    """Código curto para caber na coluna Pag. do PDF."""
    f = (forma or "").strip().lower()
    if " + " in f:
        partes = [_codigo_pagamento_pdf(p.strip()) for p in f.split(" + ")]
        partes = [p for p in partes if p and p != "—"]
        return "+".join(partes) if partes else "—"
    if not f or f == "—":
        return "—"
    if f == "pix":
        return "PIX"
    if "dinheiro" in f:
        return "DIN"
    if "crédito" in f or "credito" in f:
        return "CC"
    if "débito" in f or "debito" in f:
        return "CD"
    if "transfer" in f:
        return "TRF"
    if "cartão" in f or "cartao" in f:
        return "CAR"
    return (forma or "—")[:4].upper()


def _fmt_regra_comissao(modo: str, regra: str) -> str:
    """Ex.: R$ 188,00 (fixo) ou 30,00% (%)"""
    if not regra:
        return "—"
    if modo == "fixo":
        return f"{regra} (fixo)"
    if modo == "percentual":
        return f"{regra} (%)"
    return regra
