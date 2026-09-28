"""Filtros e totais da lista de consultas (controle financeiro da secretaria)."""
from __future__ import annotations

from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils.dateparse import parse_date

from .models.financeiro import Payment, PaymentParcela

TZ_CLINICA = ZoneInfo("America/Sao_Paulo")


def filtrar_consultas_lista(qs, params):
    """Aplica paciente, profissional, status, fila e período (data do agendamento)."""
    from .views_consultas.helpers import aplicar_ordem_fila_iniciar, q_consultas_aguardando_inicio

    if patient_id := params.get("patient"):
        qs = qs.filter(patient_id=patient_id)
    if professional_id := params.get("professional"):
        qs = qs.filter(professional_id=professional_id)
    if st := params.get("status"):
        qs = qs.filter(status=st)
    if appointment_id := params.get("appointment"):
        qs = qs.filter(appointment_id=appointment_id)

    inicio = parse_date(str(params.get("data_inicio") or "")) if params.get("data_inicio") else None
    fim = parse_date(str(params.get("data_fim") or "")) if params.get("data_fim") else None
    if inicio or fim:
        qs = qs.annotate(
            data_lista=TruncDate(
                Coalesce("appointment__date", "data_inicio"),
                tzinfo=TZ_CLINICA,
            ),
        )
        if inicio:
            qs = qs.filter(data_lista__gte=inicio)
        if fim:
            qs = qs.filter(data_lista__lte=fim)

    if (params.get("fila") or "").strip().lower() == "iniciar":
        qs = aplicar_ordem_fila_iniciar(qs.filter(q_consultas_aguardando_inicio()))
    elif (params.get("ordem") or "").strip().lower() == "nome":
        qs = qs.order_by("patient__nome", "patient_id", "-data_inicio", "-id")
    return qs


def resumo_financeiro_consultas(qs) -> dict:
    """Soma o que já entrou e o saldo em aberto das consultas filtradas."""
    pago_sq = (
        PaymentParcela.objects.filter(payment_id=OuterRef("pk"), status="PAID")
        .values("payment_id")
        .annotate(total=Sum("valor"))
        .values("total")[:1]
    )
    payments = (
        Payment.objects.filter(appointment_id__in=qs.values("appointment_id"))
        .exclude(status="CANCELLED")
        .annotate(
            pago_parcelas=Coalesce(
                Subquery(pago_sq, output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0")),
            ),
        )
    )
    total_pago = Decimal("0")
    a_receber = Decimal("0")
    for payment in payments.iterator(chunk_size=500):
        pago = Decimal(str(payment.pago_parcelas or 0))
        if pago <= 0 and payment.status in ("PAID", "PARTIAL", "DRAFT"):
            pago = Decimal(str(payment.amount or 0))
        total = payment.valor_total if payment.valor_total is not None else Decimal(str(payment.amount or 0))
        total_pago += pago
        saldo = total - pago
        if saldo > 0:
            a_receber += saldo
    return {"total_pago": float(total_pago), "a_receber": float(a_receber)}
