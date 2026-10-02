"""Correção da forma de um recebimento já pago.

Não grava nada e não importa o Django: só decide o que pode mudar.
Trocar dinheiro, PIX ou cartão não mexe em valor nem status.
Passar para a prazo desfaz o recebimento: o valor volta a ficar em aberto.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Dinheiro que já entrou. A prazo entra à parte: tira o valor do recebido.
FORMAS_PAGAMENTO_CORRIGIVEIS = frozenset({
    "CASH",
    "CREDIT_CARD",
    "DEBIT_CARD",
    "PIX",
    "TRANSFER",
    "PRAZO",
})


def _decimal_forma(valor) -> Decimal:
    try:
        return Decimal(str(valor if valor is not None else 0))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)


def _chave_parcela_forma(parcela: dict):
    quando = parcela.get("payment_date") or date.min
    if isinstance(quando, datetime):
        quando = quando.date()
    return (quando, parcela.get("id") or 0)


def _metodo_exibido_pelas_parcelas(parcelas: list[dict], fallback: str) -> str:
    if not parcelas:
        return fallback
    metodos = {p["payment_method"] for p in parcelas}
    if len(metodos) == 1:
        return next(iter(metodos))
    ultima = max(parcelas, key=_chave_parcela_forma)
    return ultima["payment_method"]


def plano_correcao_forma_pagamento(
    *,
    status: str,
    payment_method: str,
    amount,
    parcelas: list[dict],
    nova_forma: str,
    parcela_id: int | None = None,
) -> dict:
    """Decide a correção da forma.

    ``parcelas`` são só as já pagas: id, payment_method, payment_date, valor.
    Troca entre formas recebidas devolve o mapa de parcelas que mudam.
    ``virar_prazo`` desfaz o recebimento inteiro e cancela essas parcelas.
    """
    forma = (nova_forma or "").strip()
    if forma not in FORMAS_PAGAMENTO_CORRIGIVEIS:
        raise ValueError(
            "Escolha dinheiro, PIX, cartão, transferência ou a prazo.",
        )
    if status not in ("PAID", "PARTIAL"):
        raise ValueError("Só dá para corrigir a forma de um recebimento já pago.")
    if payment_method in ("DESPESA", "PRAZO"):
        raise ValueError("Esta forma não pode ser alterada por aqui.")
    if any(p.get("payment_method") == "DESPESA" for p in parcelas):
        raise ValueError("Esta forma não pode ser alterada por aqui.")

    total = sum((_decimal_forma(p.get("valor")) for p in parcelas), Decimal(0))
    if total <= Decimal("0.01"):
        total = _decimal_forma(amount)
    if total <= Decimal("0.01"):
        raise ValueError("Este atendimento não teve recebimento para corrigir.")

    if forma == "PRAZO":
        if parcela_id is not None:
            raise ValueError("A prazo vale para o atendimento inteiro, não para um lançamento.")
        return {
            "alterado": True,
            "payment_method": "PRAZO",
            "parcelas": {},
            "virar_prazo": True,
            "parcelas_cancelar": [p["id"] for p in parcelas],
        }

    if any(p.get("payment_method") == "PRAZO" for p in parcelas):
        raise ValueError("Esta forma não pode ser alterada por aqui.")

    if parcela_id is not None:
        alvo = next((p for p in parcelas if p.get("id") == parcela_id), None)
        if alvo is None:
            raise LookupError("Lançamento não encontrado neste pagamento.")
        atualizados = [
            {**p, "payment_method": forma if p.get("id") == parcela_id else p["payment_method"]}
            for p in parcelas
        ]
        novo_header = _metodo_exibido_pelas_parcelas(atualizados, forma)
        parcelas_novas = {parcela_id: forma} if alvo["payment_method"] != forma else {}
        if not parcelas_novas and payment_method == novo_header:
            return {"alterado": False, "payment_method": payment_method, "parcelas": {}}
        return {
            "alterado": True,
            "payment_method": novo_header,
            "parcelas": parcelas_novas,
        }

    metodos = {p["payment_method"] for p in parcelas}
    if len(metodos) > 1:
        raise ValueError("Este recebimento tem mais de uma forma. Corrija cada lançamento.")
    ja_esta = (not metodos or next(iter(metodos)) == forma) and payment_method == forma
    if ja_esta:
        return {"alterado": False, "payment_method": payment_method, "parcelas": {}}
    return {
        "alterado": True,
        "payment_method": forma,
        "parcelas": {p["id"]: forma for p in parcelas if p["payment_method"] != forma},
    }
