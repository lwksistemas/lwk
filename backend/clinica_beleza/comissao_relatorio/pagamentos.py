from decimal import Decimal


def _agrupar_pagamentos_por_agendamento(payments) -> list[dict]:
    """Consolida pagamentos do mesmo agendamento (ex.: parte no débito e parte no crédito).
    Evita contar a mesma consulta duas vezes no relatório.
    """
    grupos: dict[int, dict] = {}
    ordem: list[int] = []
    for payment in payments:
        appt = getattr(payment, "appointment", None)
        if not appt:
            continue
        appt_id = appt.id
        if appt_id not in grupos:
            grupos[appt_id] = {
                "appointment": appt,
                "payments": [],
                "total_amount": Decimal(0),
            }
            ordem.append(appt_id)
        grupos[appt_id]["payments"].append(payment)
        grupos[appt_id]["total_amount"] += payment.amount or Decimal(0)
    return [grupos[aid] for aid in ordem]


def _obter_ou_criar_detalhe(entry: dict, chave: str, defaults: dict) -> dict:
    detalhe = next((d for d in entry["detalhes"] if d["_chave"] == chave), None)
    if detalhe:
        return detalhe
    detalhe = {"_chave": chave, **defaults}
    entry["detalhes"].append(detalhe)
    return detalhe
