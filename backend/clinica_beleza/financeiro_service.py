"""Regras do financeiro da clínica — listagem, resumo, parcelas e exclusão."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Case, DecimalField, Exists, F, OuterRef, Prefetch, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Greatest
from django.utils.timezone import now

from .models import CategoriaDespesa, ConsultaEvolucao, Despesa, Payment
from .models.financeiro import CATEGORIAS_DESPESA_PADRAO, PaymentParcela

_DEC = DecimalField(max_digits=14, decimal_places=2)
METODO_DESPESA = "DESPESA"


def payments_visiveis_financeiro(qs=None):
    """Financeiro só mostra lançamentos de consultas finalizadas.
    Rascunhos (DRAFT) do Receber ficam só na consulta até Finalizar.
    Agendamento cancelado não entra na lista nem em A receber.
    """
    if qs is None:
        qs = Payment.objects.all()
    return (
        qs.exclude(status="DRAFT")
        .exclude(appointment__status="CANCELLED")
        .filter(
            Q(appointment__consulta__status="COMPLETED") | Q(appointment__consulta__isnull=True),
        )
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


def _nome_procedimento_payment(payment) -> str:
    appt = getattr(payment, "appointment", None)
    if not appt:
        return ""
    prefetched = getattr(appt, "_prefetched_objects_cache", {}).get("appointment_procedures")
    if prefetched is not None:
        nomes = [
            ap.procedure.nome
            for ap in prefetched
            if getattr(getattr(ap, "procedure", None), "nome", None)
        ]
        if nomes:
            return " · ".join(nomes)
    procedure = getattr(appt, "procedure", None)
    return getattr(procedure, "nome", "") or ""


def listar_a_receber_periodo(first_day: date, last_day: date) -> tuple[float, list[dict]]:
    """Saldos em aberto de atendimentos do mês, do maior para o menor."""
    base = payments_visiveis_financeiro(
        Payment.objects.select_related(
            "appointment",
            "appointment__patient",
            "appointment__procedure",
        ).prefetch_related("appointment__appointment_procedures__procedure"),
    ).filter(
        status__in=("PENDING", "PARTIAL"),
        appointment__date__date__gte=first_day,
        appointment__date__date__lte=last_day,
    )
    anotados = (
        _anotar_saldo_em_aberto(base)
        .filter(_saldo__gt=Decimal("0.01"))
        .order_by("-_saldo", "appointment__date")
    )
    itens: list[dict] = []
    total = Decimal(0)
    for payment in anotados:
        saldo = Decimal(str(getattr(payment, "_saldo", 0) or 0))
        total += saldo
        patient = getattr(payment.appointment, "patient", None)
        itens.append({
            "paciente": getattr(patient, "nome", "") or "—",
            "procedimento": _nome_procedimento_payment(payment) or "—",
            "saldo": float(saldo),
        })
    return float(total), itens


def somar_a_receber_periodo(first_day: date, last_day: date, *, payment_method: str | None = None) -> float:
    """Soma o saldo em aberto dos atendimentos do mês. Com método, só essa forma."""
    base = payments_visiveis_financeiro().filter(
        status__in=("PENDING", "PARTIAL"),
        appointment__date__date__gte=first_day,
        appointment__date__date__lte=last_day,
    )
    if payment_method:
        base = base.filter(payment_method=payment_method)
    agregado = _anotar_saldo_em_aberto(base).aggregate(t=Sum("_saldo"))
    return float(agregado["t"] or 0)


def somar_desconto_periodo(first_day: date, last_day: date) -> float:
    """Desconto comercial dos atendimentos do mês."""
    total = payments_visiveis_financeiro(
        Payment.objects.filter(
            appointment__date__date__gte=first_day,
            appointment__date__date__lte=last_day,
            desconto__gt=0,
        ),
    ).exclude(status="CANCELLED").aggregate(t=Sum("desconto"))["t"]
    return float(total or 0)


def _anotar_saldo_em_aberto(base):
    """Anota _saldo (valor total - pago) nos payments PENDING/PARTIAL da base."""
    pago_sub = (
        PaymentParcela.objects.filter(payment_id=OuterRef("pk"), status="PAID")
        .values("payment_id")
        .annotate(s=Sum("valor"))
        .values("s")[:1]
    )
    return (
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
    )


def queryset_inadimplentes(qs=None, *, hoje: date | None = None):
    """Payments a prazo vencidos e com saldo em aberto (inadimplência).

    Vencido = status PENDING/PARTIAL, data_vencimento < hoje e _saldo > 0.
    """
    hoje = hoje or now().date()
    base = payments_visiveis_financeiro(qs).filter(
        status__in=("PENDING", "PARTIAL"),
        data_vencimento__isnull=False,
        data_vencimento__lt=hoje,
    )
    return _anotar_saldo_em_aberto(base).filter(_saldo__gt=Decimal("0.01"))


def somar_inadimplencia(qs=None, *, hoje: date | None = None) -> float:
    """Soma o saldo em aberto de todos os pagamentos vencidos (1 query)."""
    agregado = queryset_inadimplentes(qs, hoje=hoje).aggregate(t=Sum("_saldo"))
    return float(agregado["t"] or 0)


def contar_inadimplentes(qs=None, *, hoje: date | None = None) -> int:
    """Quantidade de pagamentos vencidos em aberto."""
    return queryset_inadimplentes(qs, hoje=hoje).count()


def pagamento_vencido_do_paciente(patient_id: int, *, hoje: date | None = None):
    """Retorna o pagamento vencido mais antigo do paciente, ou None."""
    if not patient_id:
        return None
    return (
        queryset_inadimplentes(hoje=hoje)
        .filter(appointment__patient_id=patient_id)
        .order_by("data_vencimento")
        .first()
    )


def paciente_em_atraso(patient_id: int, *, hoje: date | None = None) -> bool:
    """True se o paciente tem algum pagamento a prazo vencido em aberto."""
    return pagamento_vencido_do_paciente(patient_id, hoje=hoje) is not None


def mensagem_bloqueio_inadimplencia(patient_id: int, *, hoje: date | None = None) -> str | None:
    """Mensagem de bloqueio se o paciente está inadimplente; None caso contrário."""
    pgto = pagamento_vencido_do_paciente(patient_id, hoje=hoje)
    if pgto is None:
        return None
    venc = pgto.data_vencimento
    venc_txt = venc.strftime("%d/%m/%Y") if venc else "—"
    return (
        f"Paciente com pagamento em atraso desde {venc_txt}. "
        f"Regularize no Financeiro antes de agendar ou abrir uma nova consulta."
    )


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
            "appointment__retorno_procedure",
            # consulta usada para exibir "Isento" (retorno gratuito) sem N+1.
            "appointment__consulta",
        ).prefetch_related(
            "appointment__appointment_procedures__procedure",
            "parcelas",
            Prefetch(
                "appointment__consulta__evolucoes",
                queryset=ConsultaEvolucao.objects.order_by("-created_at"),
                to_attr="evolucoes_recentes",
            ),
        ),
    ).order_by("-appointment__date", "-id")
    # Lista só movimento de dinheiro. Pago com valor fica. Retorno ou consulta a R$ 0,00 não entra.
    qs = qs.filter(
        Q(valor_total__gt=0) | Q(valor_total__isnull=True, amount__gt=0),
    )
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
    if payment.status in ("PAID", "PARTIAL"):
        payment.payment_date = _datetime_do_lancamento(dados.get("payment_date"))
    update_fields = ["status", "amount", "updated_at"]
    if metodo:
        update_fields.append("payment_method")
    if payment.status in ("PAID", "PARTIAL"):
        update_fields.append("payment_date")
    if payment.status == "PAID":
        # Quitado deixa de ser conta a receber a prazo.
        if payment.data_vencimento:
            payment.data_vencimento = None
            update_fields.append("data_vencimento")
    elif metodo == "PRAZO":
        # Baixa "a prazo" no Financeiro: carimba o vencimento a partir de hoje.
        venc = _calcular_vencimento_baixa_prazo(payment)
        if venc != payment.data_vencimento:
            payment.data_vencimento = venc
            update_fields.append("data_vencimento")
    payment.save(update_fields=update_fields)
    return parcela


def _datetime_do_lancamento(raw):
    """Data escolhida no Registrar Pagamento, no fuso da clínica."""
    from datetime import datetime

    from django.utils.timezone import get_current_timezone, make_aware

    if isinstance(raw, datetime):
        return raw if raw.tzinfo else make_aware(raw, get_current_timezone())
    text = str(raw or "").strip()[:10]
    try:
        dia = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return now()
    return make_aware(dia, get_current_timezone())


def _calcular_vencimento_baixa_prazo(payment):
    """Vencimento para baixa a prazo pelo Financeiro (base = hoje). Retorna date ou None."""
    appointment = getattr(payment, "appointment", None)
    patient = getattr(appointment, "patient", None)
    if patient is None:
        return None
    from .prazo_service import PrazoNaoConfiguradoError, calcular_vencimento

    try:
        return calcular_vencimento(patient, now().date())
    except PrazoNaoConfiguradoError:
        return None


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
    a_receber_mes = somar_a_receber_periodo(first_day, last_day)
    a_prazo_mes = somar_a_receber_periodo(first_day, last_day, payment_method="PRAZO")
    desconto_mes = somar_desconto_periodo(first_day, last_day)
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
        "a_receber": a_receber_mes,
        "desconto": desconto_mes,
        "a_prazo": a_prazo_mes,
        "filter": {"mes": mes, "ano": ano},
    }
