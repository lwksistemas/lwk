"""Relatório de descontos concedidos no Receber — por profissional, com clientes."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from .financeiro_service import payments_visiveis_financeiro
from .serializers.financeiro import _procedimentos_nome_agendamento


def calcular_descontos(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
) -> dict:
    """Lista atendimentos com desconto comercial, agrupados por profissional."""
    qs = (
        payments_visiveis_financeiro()
        .exclude(status="CANCELLED")
        .filter(desconto__gt=0)
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

    grupos: dict[int, dict] = defaultdict(lambda: {
        "professional_id": 0,
        "nome": "Sem profissional",
        "total_atendimentos": 0,
        "desconto_total": Decimal(0),
        "valor_bruto": Decimal(0),
        "valor_liquido": Decimal(0),
        "lancamentos": [],
    })

    for payment in qs:
        appt = payment.appointment
        if not appt:
            continue
        desconto = Decimal(str(payment.desconto or 0))
        if desconto <= 0:
            continue
        liquido = Decimal(str(payment.valor_total_efetivo or payment.amount or 0))
        bruto = liquido + desconto
        pid = appt.professional_id or 0
        grupo = grupos[pid]
        grupo["professional_id"] = pid
        if appt.professional_id and appt.professional:
            grupo["nome"] = appt.professional.nome
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
            "valor_bruto": float(bruto),
            "desconto": float(desconto),
            "valor_liquido": float(liquido),
        })
        grupo["total_atendimentos"] += 1
        grupo["desconto_total"] += desconto
        grupo["valor_bruto"] += bruto
        grupo["valor_liquido"] += liquido

    profissionais = sorted(grupos.values(), key=lambda g: (g["nome"] or "").lower())
    for p in profissionais:
        p["desconto_total"] = float(p["desconto_total"])
        p["valor_bruto"] = float(p["valor_bruto"])
        p["valor_liquido"] = float(p["valor_liquido"])

    return {
        "profissionais": profissionais,
        "totais": {
            "total_atendimentos": sum(p["total_atendimentos"] for p in profissionais),
            "desconto_total": sum(p["desconto_total"] for p in profissionais),
            "valor_bruto": sum(p["valor_bruto"] for p in profissionais),
            "valor_liquido": sum(p["valor_liquido"] for p in profissionais),
        },
    }
