"""Relatório de inadimplentes: pagamentos a prazo vencidos e em aberto.

Fonte: Payment PENDING/PARTIAL com data_vencimento < hoje e saldo > 0.
Cada linha traz paciente, contato, valor em aberto, vencimento e dias de atraso.
"""
from __future__ import annotations

from datetime import date

from django.utils.timezone import now

from .financeiro_service import queryset_inadimplentes


def _serialize_linha(payment, hoje: date) -> dict:
    appointment = getattr(payment, "appointment", None)
    patient = getattr(appointment, "patient", None)
    venc = payment.data_vencimento
    dias_atraso = (hoje - venc).days if venc else 0
    try:
        saldo = float(payment.saldo_devedor)
    except Exception:
        saldo = float(payment.amount or 0)
    return {
        "payment_id": payment.id,
        "patient_id": getattr(patient, "id", None),
        "paciente_nome": getattr(patient, "nome", "") or "",
        "telefone": getattr(patient, "telefone", "") or "",
        "email": getattr(patient, "email", "") or "",
        "valor_aberto": saldo,
        "vencimento": venc.isoformat() if venc else None,
        "dias_atraso": max(0, dias_atraso),
        "status": payment.status,
    }


def calcular_inadimplentes(*, hoje: date | None = None) -> dict:
    """Retorna dict com 'linhas' (ordenadas por mais atrasado) e 'totais'."""
    hoje = hoje or now().date()
    qs = (
        queryset_inadimplentes(hoje=hoje)
        .select_related("appointment__patient")
        .order_by("data_vencimento")
    )

    linhas = [_serialize_linha(p, hoje) for p in qs]

    totais = {
        "total_inadimplentes": len(linhas),
        "valor_total": round(sum(linha["valor_aberto"] for linha in linhas), 2),
    }
    return {"linhas": linhas, "totais": totais}
