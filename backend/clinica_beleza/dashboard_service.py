"""Service de KPIs do dashboard — Clínica da Beleza.

Agrega estatísticas, faturamento diário, top procedimentos e próximos agendamentos.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDay
from django.utils.timezone import now

from .models import Appointment, AppointmentProcedure, Consulta, Patient, Payment, Procedure

MESES_PT = (
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)

SOROTERAPIA_PROCEDURE_Q = (
    Q(procedure__categoria__iexact="soroterapia")
    | Q(procedure__categoria__icontains="soroterapia")
    | Q(procedure__categoria__iexact="injetavel")
    | Q(procedure__categoria__icontains="injetavel")
)

SOROTERAPIA_CADASTRO_Q = (
    Q(categoria__iexact="soroterapia")
    | Q(categoria__icontains="soroterapia")
    | Q(categoria__iexact="injetavel")
    | Q(categoria__icontains="injetavel")
)

NEXT_APPOINTMENT_STATUSES = (
    "SCHEDULED", "CLIENT_CONFIRMED", "PHONE_CONFIRMED", "CONFIRMED", "IN_PROGRESS",
)

VOLUME_APPOINTMENT_STATUSES = (
    "COMPLETED", "CONFIRMED", "CLIENT_CONFIRMED", "PHONE_CONFIRMED", "SCHEDULED", "IN_PROGRESS",
)


def parse_dashboard_period(
    *,
    mes: int | None,
    ano: int | None,
    today: date,
) -> tuple[date, date, int, int]:
    """Intervalo do filtro mensal (mes/ano). No mês atual, termina em today."""
    try:
        ano_res = int(ano or today.year)
        mes_res = int(mes or today.month)
        if not (1 <= mes_res <= 12):
            raise ValueError("mes invalido")
    except (ValueError, TypeError):
        ano_res, mes_res = today.year, today.month

    first_day = date(ano_res, mes_res, 1)
    last_day = date(ano_res, mes_res, calendar.monthrange(ano_res, mes_res)[1])
    if ano_res == today.year and mes_res == today.month:
        period_end = today
    else:
        period_end = last_day

    return first_day, period_end, mes_res, ano_res


def dashboard_filter_meta(*, filter_mes: int, filter_ano: int, today: date, period_start: date, period_end: date) -> dict:
    return {
        "mes": filter_mes,
        "ano": filter_ano,
        "label": f"{MESES_PT[filter_mes]}/{filter_ano}",
        "is_current_month": filter_ano == today.year and filter_mes == today.month,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }


def backfill_consultas_data_fim():
    """Consultas concluídas sem data_fim (legado) — usa updated_at para o dashboard."""
    Consulta.objects.filter(status="COMPLETED", data_fim__isnull=True).update(data_fim=F("updated_at"))


def consulta_realizada_no_periodo_q(period_start: date, period_end: date) -> Q:
    """Consulta concluída no intervalo se data_fim, updated_at ou agendamento cair nele."""

    def in_period(prefix: str) -> Q:
        return (
            Q(**{f"{prefix}__date__gte": period_start})
            & Q(**{f"{prefix}__date__lte": period_end})
        )

    return (
        in_period("data_fim")
        | in_period("updated_at")
        | in_period("appointment__date")
    )


def consultas_concluidas_no_periodo(period_start: date, period_end: date):
    return Consulta.objects.filter(status="COMPLETED").filter(
        consulta_realizada_no_periodo_q(period_start, period_end),
    )


def revenue_by_day(first_day: date, period_end: date) -> list[dict]:
    """Faturamento por dia usando agregação SQL (uma query em vez de N)."""
    rows_db = (
        Payment.objects
        .filter(status="PAID", payment_date__date__gte=first_day, payment_date__date__lte=period_end)
        .annotate(day=TruncDay("payment_date"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )
    revenue_map = {row["day"].date(): float(row["total"]) for row in rows_db}

    rows = []
    day = first_day
    while day <= period_end:
        rows.append({"day": day.strftime("%d/%m"), "value": revenue_map.get(day, 0)})
        day += timedelta(days=1)
    return rows


def top_procedures_realizados_periodo(period_start: date, period_end: date) -> list[dict]:
    rows = (
        consultas_concluidas_no_periodo(period_start, period_end)
        .filter(procedure__isnull=False)
        .values("procedure__nome")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    return [
        {"name": item["procedure__nome"] or "Consulta", "count": item["count"]}
        for item in rows
    ]


def top_soroterapia_periodo(period_start: date, period_end: date) -> list[dict]:
    """Top soroterapias no mês: consultas concluídas + agendamentos (volume).
    Se não houver movimento, lista cadastros ativos de soroterapia (count=0).
    """
    counts: dict[str, int] = {}

    def add_rows(rows):
        for item in rows:
            name = item["procedure__nome"] or "Sem nome"
            counts[name] = counts.get(name, 0) + item["count"]

    add_rows(
        consultas_concluidas_no_periodo(period_start, period_end)
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values("procedure__nome")
        .annotate(count=Count("id")),
    )
    add_rows(
        Appointment.objects.filter(
            date__date__gte=period_start,
            date__date__lte=period_end,
            status__in=VOLUME_APPOINTMENT_STATUSES,
        )
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values("procedure__nome")
        .annotate(count=Count("id")),
    )
    add_rows(
        AppointmentProcedure.objects.filter(
            appointment__date__date__gte=period_start,
            appointment__date__date__lte=period_end,
            appointment__status__in=VOLUME_APPOINTMENT_STATUSES,
        )
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values("procedure__nome")
        .annotate(count=Count("id")),
    )

    ranked = sorted(
        [{"name": name, "count": count} for name, count in counts.items() if count > 0],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    if ranked:
        return ranked

    cadastros = (
        Procedure.objects.filter(is_active=True)
        .filter(SOROTERAPIA_CADASTRO_Q)
        .order_by("nome")
        .values_list("nome", flat=True)[:5]
    )
    return [{"name": nome, "count": 0} for nome in cadastros]


def build_dashboard_statistics(*, today: date, period_start: date, period_end: date) -> dict:
    """Agrega métricas numéricas do dashboard para o período."""
    yesterday = today - timedelta(days=1)
    revenue_month = Payment.objects.filter(
        status="PAID",
        payment_date__date__gte=period_start,
        payment_date__date__lte=period_end,
    ).aggregate(total=Sum("amount"))["total"] or 0
    revenue_today = Payment.objects.filter(
        status="PAID", payment_date__date=today,
    ).aggregate(total=Sum("amount"))["total"] or 0
    return {
        "appointments_today": Appointment.objects.filter(date__date=today).count(),
        "appointments_yesterday": Appointment.objects.filter(date__date=yesterday).count(),
        "patients_total": Patient.objects.filter(is_active=True).count(),
        "procedures_total": Procedure.objects.filter(is_active=True).count(),
        "revenue_month": float(revenue_month),
        "revenue_today": float(revenue_today),
        "sessions_month": consultas_concluidas_no_periodo(period_start, period_end).count(),
    }


def next_appointments_queryset(
    *,
    period: str,
    professional_id: int | None,
    today: date,
    current: datetime,
):
    """Queryset dos próximos agendamentos conforme período (sem slice)."""
    if period == "hoje":
        next_qs = Appointment.objects.filter(date__date=today, date__gte=current)
    else:
        days_ahead = 7 if period == "semana" else 14
        horizon = today + timedelta(days=days_ahead)
        next_qs = Appointment.objects.filter(date__gte=current, date__date__lte=horizon)

    next_qs = next_qs.filter(
        status__in=NEXT_APPOINTMENT_STATUSES,
    ).select_related("patient", "professional", "procedure").order_by("date")

    if professional_id is not None:
        next_qs = next_qs.filter(professional_id=professional_id)

    return next_qs


def next_appointments_limit(period: str) -> int:
    return 10 if period == "hoje" else 15


def parse_next_appointments_period(period_raw: str | None) -> str:
    return (period_raw or "proximos").strip().lower()


def parse_professional_id(professional_raw: str | None) -> int | None:
    if not professional_raw:
        return None
    try:
        return int(professional_raw)
    except (ValueError, TypeError):
        return None


def build_dashboard_data(
    *,
    mes: int | None,
    ano: int | None,
    period_raw: str | None,
    professional_raw: str | None,
    today: date | None = None,
    current: datetime | None = None,
) -> dict:
    """Monta payload completo do dashboard (sem cache)."""
    today = today or now().date()
    current = current or now()
    period_start, period_end, filter_mes, filter_ano = parse_dashboard_period(
        mes=mes, ano=ano, today=today,
    )
    period = parse_next_appointments_period(period_raw)
    professional_id = parse_professional_id(professional_raw)

    return {
        "filter": dashboard_filter_meta(
            filter_mes=filter_mes,
            filter_ano=filter_ano,
            today=today,
            period_start=period_start,
            period_end=period_end,
        ),
        "statistics": build_dashboard_statistics(
            today=today, period_start=period_start, period_end=period_end,
        ),
        "revenue_last_7_days": revenue_by_day(period_start, period_end),
        "top_procedures": top_procedures_realizados_periodo(period_start, period_end),
        "top_procedures_volume": top_soroterapia_periodo(period_start, period_end),
        "_next_appointments_meta": {
            "period": period,
            "professional_id": professional_id,
            "today": today,
            "current": current,
            "limit": next_appointments_limit(period),
        },
    }
