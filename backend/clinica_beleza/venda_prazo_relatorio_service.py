"""Relatório de venda a prazo — por período e por profissional.

Fonte: saldo em aberto de venda a prazo no dia do agendamento.
Entra a forma A prazo e também o que já teve entrada, mas ainda guarda vencimento.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.timezone import now

from .financeiro_service import payments_visiveis_financeiro
from .serializers.financeiro import _procedimentos_nome_agendamento


def _dinheiro(valor) -> float:
    try:
        return float(Decimal(str(valor or 0)).quantize(Decimal("0.01")))
    except (InvalidOperation, TypeError, ValueError):
        return 0.0


def _numero_consulta(appt) -> int | None:
    try:
        consulta = appt.consulta
    except (ObjectDoesNotExist, AttributeError):
        return None
    numero = getattr(consulta, "numero", None) if consulta is not None else None
    try:
        return int(numero) if numero else None
    except (TypeError, ValueError):
        return None


def _situacao(vencimento: date | None, hoje: date) -> tuple[str, str, int]:
    if not vencimento:
        return "sem_vencimento", "Sem vencimento", 0
    if vencimento < hoje:
        return "vencido", "Vencido", (hoje - vencimento).days
    return "em_dia", "Em dia", 0


def calcular_venda_prazo(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
    hoje: date | None = None,
) -> dict:
    """Vendas a prazo do período, agrupadas pelo profissional do agendamento."""
    hoje = hoje or now().date()
    qs = (
        payments_visiveis_financeiro()
        .filter(status__in=("PENDING", "PARTIAL"))
        .filter(Q(payment_method="PRAZO") | Q(data_vencimento__isnull=False))
        .select_related(
            "appointment__professional",
            "appointment__patient",
            "appointment__consulta",
        )
        .prefetch_related(
            "parcelas",
            "appointment__appointment_procedures__procedure",
        )
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
        "total_vendas": 0,
        "valor_total": Decimal(0),
        "valor_pago": Decimal(0),
        "valor_aberto": Decimal(0),
        "vendas": [],
    })
    clientes: dict[int | str, dict] = defaultdict(lambda: {
        "patient_id": 0,
        "nome": "—",
        "telefone": "",
        "total_consultas": 0,
        "valor_total": Decimal(0),
        "valor_pago": Decimal(0),
        "valor_aberto": Decimal(0),
        "consultas": [],
    })

    for payment in qs:
        appt = payment.appointment
        if not appt:
            continue
        try:
            saldo = Decimal(str(payment.saldo_devedor or 0))
        except (TypeError, ArithmeticError, InvalidOperation):
            saldo = Decimal(0)
        if saldo <= Decimal("0.01"):
            continue
        try:
            pago = Decimal(str(payment.valor_pago_parcelas or 0))
        except (TypeError, ArithmeticError, InvalidOperation):
            pago = Decimal(0)
        try:
            total = Decimal(str(payment.valor_total_efetivo or payment.amount or 0))
        except (TypeError, ArithmeticError, InvalidOperation):
            total = saldo

        pid = appt.professional_id or 0
        grupo = grupos[pid]
        grupo["professional_id"] = pid
        if appt.professional_id and appt.professional:
            grupo["nome"] = appt.professional.nome

        patient = appt.patient if appt.patient_id else None
        paciente_nome = getattr(patient, "nome", "") or "—"
        telefone = getattr(patient, "telefone", "") or ""
        profissional_nome = grupo["nome"]
        venc = payment.data_vencimento
        codigo, rotulo, dias = _situacao(venc, hoje)
        dt = appt.date
        linha = {
            "payment_id": payment.id,
            "data": dt.date().isoformat() if dt else None,
            "patient_id": appt.patient_id or 0,
            "paciente": paciente_nome,
            "telefone": telefone,
            "profissional": profissional_nome,
            "consulta_numero": _numero_consulta(appt),
            "procedimentos": _procedimentos_nome_agendamento(appt) or "Consulta",
            "vencimento": venc.isoformat() if venc else None,
            "situacao": codigo,
            "situacao_label": rotulo,
            "dias_atraso": dias,
            "valor": _dinheiro(total),
            "valor_pago": _dinheiro(pago),
            "valor_aberto": _dinheiro(saldo),
        }
        grupo["vendas"].append(linha)
        grupo["total_vendas"] += 1
        grupo["valor_total"] += total
        grupo["valor_pago"] += pago
        grupo["valor_aberto"] += saldo

        chave = appt.patient_id or paciente_nome
        cliente = clientes[chave]
        cliente["patient_id"] = appt.patient_id or 0
        cliente["nome"] = paciente_nome
        cliente["telefone"] = telefone
        cliente["consultas"].append(linha)
        cliente["total_consultas"] += 1
        cliente["valor_total"] += total
        cliente["valor_pago"] += pago
        cliente["valor_aberto"] += saldo

    profissionais = sorted(grupos.values(), key=lambda g: (g["nome"] or "").lower())
    for p in profissionais:
        p["valor_total"] = _dinheiro(p["valor_total"])
        p["valor_pago"] = _dinheiro(p["valor_pago"])
        p["valor_aberto"] = _dinheiro(p["valor_aberto"])

    lista_clientes = sorted(clientes.values(), key=lambda g: (g["nome"] or "").lower())
    for c in lista_clientes:
        c["valor_total"] = _dinheiro(c["valor_total"])
        c["valor_pago"] = _dinheiro(c["valor_pago"])
        c["valor_aberto"] = _dinheiro(c["valor_aberto"])

    return {
        "profissionais": profissionais,
        "clientes": lista_clientes,
        "totais": {
            "total_vendas": sum(p["total_vendas"] for p in profissionais),
            "valor_total": round(sum(p["valor_total"] for p in profissionais), 2),
            "valor_pago": round(sum(p["valor_pago"] for p in profissionais), 2),
            "valor_aberto": round(sum(p["valor_aberto"] for p in profissionais), 2),
        },
    }
