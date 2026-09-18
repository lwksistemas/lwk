"""Relatório de lançamentos do financeiro — por profissional, com pacientes."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from .financeiro_service import payments_visiveis_financeiro
from .models import Payment
from .models.financeiro import status_pagamento_exibido
from .serializers.financeiro import _procedimentos_nome_agendamento


def _forma_label(method: str) -> str:
    return dict(Payment.PAYMENT_METHOD_CHOICES).get(method or "", method or "—")


def calcular_lancamentos(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
    forma: str | None = None,
) -> dict:
    """Lista lançamentos visíveis no Financeiro, agrupados por profissional."""
    qs = (
        payments_visiveis_financeiro()
        .exclude(status="CANCELLED")
        .select_related(
            "appointment__professional",
            "appointment__patient",
            "appointment__convenio",
        )
        .prefetch_related("appointment__appointment_procedures__procedure")
        .order_by("appointment__professional__nome", "appointment__date", "id")
    )

    if data_inicio:
        qs = qs.filter(appointment__date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(appointment__date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)
    if forma:
        qs = qs.filter(payment_method=forma)

    grupos: dict[int, dict] = defaultdict(lambda: {
        "professional_id": 0,
        "nome": "Sem profissional",
        "total_atendimentos": 0,
        "valor_total": Decimal(0),
        "comissao_total": Decimal(0),
        "lancamentos": [],
    })

    for payment in qs:
        appt = payment.appointment
        if not appt:
            continue
        pid = appt.professional_id or 0
        grupo = grupos[pid]
        grupo["professional_id"] = pid
        if appt.professional_id and appt.professional:
            grupo["nome"] = appt.professional.nome
        valor = Decimal(str(payment.valor_total_efetivo or payment.amount or 0))
        comissao = Decimal(str(payment.comissao_valor or 0))
        paciente = getattr(appt.patient, "nome", "") if appt.patient_id else "—"
        convenio = ""
        if appt.convenio_id and appt.convenio:
            convenio = appt.convenio.nome
        dt = appt.date
        grupo["lancamentos"].append({
            "payment_id": payment.id,
            "data": dt.date().isoformat() if dt else None,
            "paciente": paciente,
            "procedimentos": _procedimentos_nome_agendamento(appt) or "Consulta",
            "convenio": convenio or "Particular",
            "forma_pagamento": payment.payment_method or "",
            "forma_pagamento_label": _forma_label(payment.payment_method or ""),
            "status": status_pagamento_exibido(payment),
            "valor": float(valor),
            "comissao": float(comissao),
        })
        grupo["total_atendimentos"] += 1
        grupo["valor_total"] += valor
        grupo["comissao_total"] += comissao

    profissionais = sorted(grupos.values(), key=lambda g: (g["nome"] or "").lower())
    for p in profissionais:
        p["valor_total"] = float(p["valor_total"])
        p["comissao_total"] = float(p["comissao_total"])

    return {
        "profissionais": profissionais,
        "totais": {
            "total_atendimentos": sum(p["total_atendimentos"] for p in profissionais),
            "valor_total": sum(p["valor_total"] for p in profissionais),
            "comissao_total": sum(p["comissao_total"] for p in profissionais),
        },
    }
