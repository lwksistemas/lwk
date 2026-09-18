"""Regras do financeiro da clínica — listagem, resumo, parcelas e exclusão."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Case, DecimalField, Exists, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Greatest
from django.utils.timezone import now

from .models import CategoriaDespesa, Despesa, Payment
from .models.financeiro import CATEGORIAS_DESPESA_PADRAO, PaymentParcela

_DEC = DecimalField(max_digits=14, decimal_places=2)
METODO_DESPESA = "DESPESA"


def payments_visiveis_financeiro(qs=None):
    """Financeiro só mostra lançamentos de consultas finalizadas.
    Rascunhos (DRAFT) do Receber ficam só na consulta até Finalizar.
    """
    if qs is None:
        qs = Payment.objects.all()
    return qs.exclude(status="DRAFT").filter(
        Q(appointment__consulta__status="COMPLETED") | Q(appointment__consulta__isnull=True),
    )


def somar_contas_a_receber(qs=None) -> float:
    """Soma saldo_devedor de PENDING/PARTIAL em 1 query (sem N+1 por parcela)."""
    base = payments_visiveis_financeiro(qs).filter(status__in=("PENDING", "PARTIAL"))
    pago_sub = (
        PaymentParcela.objects.filter(payment_id=OuterRef("pk"), status="PAID")
        .values("payment_id")
        .annotate(s=Sum("valor"))
        .values("s")[:1]
    )
    agregado = (
        base.annotate(
            _pago_parc=Subquery(pago_sub, output_field=_DEC),
            _total=Coalesce(F("valor_total"), F("amount"), Value(0), output_field=_DEC),
        )
        .annotate(
            _pago=Case(
                When(_pago_parc__isnull=False, then=F("_pago_parc")),
                When(
                    status__in=("PARTIAL", "PAID", "DRAFT"),
                    then=Coalesce(F("amount"), Value(0), output_field=_DEC),
                ),
                default=Value(0),
                output_field=_DEC,
            ),
        )
        .annotate(_saldo=Greatest(F("_total") - F("_pago"), Value(0), output_field=_DEC))
        .aggregate(t=Sum("_saldo"))
    )
    return float(agregado["t"] or 0)


def garantir_categorias_despesa_padrao(loja_id: int) -> None:
    if CategoriaDespesa.objects.exists():
        return
    for nome in CATEGORIAS_DESPESA_PADRAO:
        CategoriaDespesa.objects.create(loja_id=loja_id, nome=nome)


def alinhar_pendentes_com_parcela() -> None:
    """PENDING com entrada já registrada vira PARTIAL (status da lista do Financeiro)."""
    tem_pago = Exists(
        PaymentParcela.objects.filter(payment_id=OuterRef("pk"), status="PAID"),
    )
    payments_visiveis_financeiro(Payment.objects.all()).filter(status="PENDING").filter(tem_pago).update(
        status="PARTIAL",
    )


def queryset_payments_listagem(*, status=None, date_filter=None, professional_id=None):
    qs = payments_visiveis_financeiro(
        Payment.objects.select_related(
            "appointment", "appointment__patient",
            "appointment__professional", "appointment__procedure",
        ).prefetch_related(
            "appointment__appointment_procedures__procedure",
            "parcelas",
        ),
    ).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    if date_filter:
        qs = qs.filter(payment_date__date=date_filter)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)
    return qs


def decimal_ou_none(raw):
    try:
        return Decimal(str(raw or "0"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def erro_status_para_parcela(payment) -> str | None:
    if payment.status == "CANCELLED":
        return "Pagamento cancelado."
    if payment.status == "PAID":
        return "Pagamento já está quitado."
    if payment.status == "DRAFT":
        saldo = decimal_ou_none(payment.saldo_devedor) or Decimal(0)
        if saldo <= 0:
            return "Pagamento já quitado na consulta. Corrija pelo Receber ou finalize."
    return None


def erro_consulta_para_parcela(payment) -> str | None:
    consulta = getattr(getattr(payment, "appointment", None), "consulta", None)
    if consulta is not None and consulta.status != "COMPLETED":
        return (
            "Pagamento do dia da consulta é pelo Receber. "
            "Complemento em outro dia só no Financeiro após finalizar a consulta."
        )
    if consulta is None:
        return (
            "Não é possível registrar parcela neste pagamento. "
            "Finalize a consulta ou use o Receber."
        )
    return None


def aplicar_desconto_payment(payment, desconto_raw):
    desconto = decimal_ou_none(desconto_raw) or Decimal(0)
    if desconto <= 0:
        return Decimal(0)
    novo_total = max(Decimal(0), payment.valor_total_efetivo - desconto)
    payment.valor_total = novo_total
    atual = Decimal(str(payment.desconto or 0))
    payment.desconto = atual + desconto
    notas_desc = f"Desconto: R$ {desconto:.2f}"
    payment.notes = f"{payment.notes or ''}\n{notas_desc}".strip() if payment.notes else notas_desc
    payment.save(update_fields=["valor_total", "notes", "desconto", "updated_at"])
    return desconto


def criar_parcela_e_atualizar_payment(payment, valor, dados):
    parcela = None
    if valor > 0:
        parcela = PaymentParcela.objects.create(
            payment=payment,
            valor=valor,
            payment_method=dados["payment_method"],
            payment_date=dados["payment_date"],
            observacoes=dados["observacoes"],
            loja_id=payment.loja_id,
        )
    total_pago = payment.valor_pago_parcelas
    total_devedor = payment.valor_total_efetivo
    payment.status = "PAID" if total_pago >= total_devedor else "PARTIAL"
    payment.amount = total_pago
    metodo = (dados.get("payment_method") or "").strip()
    if metodo:
        payment.payment_method = metodo
    if payment.status == "PAID":
        payment.payment_date = now()
    update_fields = ["status", "amount", "updated_at"]
    if metodo:
        update_fields.append("payment_method")
    if payment.status == "PAID":
        update_fields.append("payment_date")
    payment.save(update_fields=update_fields)
    return parcela


def erro_excluir_payment(payment) -> str | None:
    """Impede apagar lançamento que já recebeu valor. PENDING sem parcela pode sair."""
    if payment.status in ("PAID", "PARTIAL"):
        return "Pagamento com valor recebido não pode ser excluído."
    if payment.parcelas.filter(status="PAID").exists():
        return "Pagamento com parcelas não pode ser excluído."
    return None


def montar_resumo_financeiro(*, ano: int, mes: int, today: date | None = None) -> dict:
    import calendar

    today = today or now().date()
    first_day = date(ano, mes, 1)
    last_day = date(ano, mes, calendar.monthrange(ano, mes)[1])
    period_end = today if (ano == today.year and mes == today.month) else last_day

    def _sum(qs):
        return float(qs.aggregate(total=Sum("amount"))["total"] or 0)

    pagos_mes = payments_visiveis_financeiro(Payment.objects.filter(
        status="PAID",
        payment_date__date__gte=first_day,
        payment_date__date__lte=period_end,
    ))
    pagos_caixa = pagos_mes.exclude(payment_method=METODO_DESPESA)
    faturamento = _sum(pagos_caixa)
    contas_a_receber = somar_contas_a_receber()
    comissao_mes = float(pagos_caixa.aggregate(total=Sum("comissao_valor"))["total"] or 0)
    despesas_atendimento = _sum(pagos_mes.filter(payment_method=METODO_DESPESA))

    def _sum_despesa(qs):
        return float(qs.aggregate(total=Sum("valor"))["total"] or 0)

    despesas_operacionais = _sum_despesa(Despesa.objects.filter(
        status="PAID",
        data_pagamento__gte=first_day,
        data_pagamento__lte=period_end,
    ))
    despesas_pendentes = _sum_despesa(Despesa.objects.filter(status="PENDING"))
    despesas_total = comissao_mes + despesas_operacionais + despesas_atendimento

    return {
        "caixa_diario": _sum(payments_visiveis_financeiro(
            Payment.objects.filter(status="PAID", payment_date__date=today),
        ).exclude(payment_method=METODO_DESPESA)),
        "total_mes": faturamento,
        "contas_a_receber": contas_a_receber,
        "comissao_mes": comissao_mes,
        "despesas_operacionais": despesas_operacionais,
        "despesas_pendentes": despesas_pendentes,
        "despesas_atendimento": despesas_atendimento,
        "faturamento": faturamento,
        "despesas": despesas_total,
        "lucro": faturamento - despesas_total,
        "filter": {"mes": mes, "ano": ano},
    }
