"""Pagamento da NF-e lido do XML (à vista, duplicatas). Não grava nada."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

_A_VISTA = {"01", "02", "03", "04", "17", "18"}
_FORMA = {
    "01": "CASH",
    "02": "CASH",
    "03": "CREDIT_CARD",
    "04": "DEBIT_CARD",
    "17": "PIX",
    "18": "TRANSFER",
    "20": "PIX",
}


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _dinheiro(valor: str) -> Decimal:
    try:
        return Decimal(str(valor or "0").replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _data_texto(valor) -> str:
    """Date do banco ou o texto já gravado no objeto."""
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor or "")[:10]


def _data(valor: str) -> str:
    texto = (valor or "")[:10]
    try:
        date.fromisoformat(texto)
    except ValueError:
        return ""
    return texto


def pagamento_da_nfe(inf_nfe, *, data_emissao: str = "", valor_total: str = "0") -> dict:
    """Lê cobr/dup e pag/detPag. Não grava nada."""
    parcelas = []
    indicadores = []
    formas = []
    for el in inf_nfe.iter():
        nome = _local(el.tag)
        if nome == "dup":
            vencimento = ""
            valor = ""
            numero = ""
            for filho in list(el):
                campo = _local(filho.tag)
                texto = (filho.text or "").strip()
                if campo == "dVenc":
                    vencimento = _data(texto)
                elif campo == "vDup":
                    valor = texto
                elif campo == "nDup":
                    numero = texto[:20]
            if vencimento and _dinheiro(valor or valor_total) > 0:
                parcelas.append({
                    "numero": numero,
                    "vencimento": vencimento,
                    "valor": str(_dinheiro(valor or valor_total).quantize(Decimal("0.01"))),
                })
        elif nome == "detPag":
            for filho in list(el):
                campo = _local(filho.tag)
                texto = (filho.text or "").strip()
                if campo == "indPag":
                    indicadores.append(texto)
                elif campo == "tPag":
                    formas.append(texto)

    forma = _FORMA.get(formas[0], "") if formas else ""
    a_vista = bool(indicadores) and all(item == "0" for item in indicadores) and "90" not in formas
    if not indicadores and formas and all(item in _A_VISTA for item in formas):
        a_vista = True
    situacao = "pendente" if parcelas else "pago" if a_vista else "indefinido"
    return {
        "situacao": situacao,
        "forma_pagamento": forma,
        "valor": str(_dinheiro(valor_total).quantize(Decimal("0.01"))),
        "data_emissao": _data(data_emissao),
        "parcelas": parcelas,
    }
