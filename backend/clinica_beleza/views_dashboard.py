"""
Views de Dashboard e Info da Loja — Clínica da Beleza
"""
import calendar
from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Count, F, Q, Sum
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_MEMBER
from rest_framework import status

from .models import Patient, Procedure, Appointment, AppointmentProcedure, Payment, Consulta
from .utils import DASHBOARD_CACHE_VERSION
from .serializers import AppointmentListSerializer
from .utils import LojaContextHelper
from tenants.middleware import get_current_loja_id

MESES_PT = (
    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
)


# Soroterapia: categoria do cadastro (ex.: "soroterapia", "Soroterapia")
SOROTERAPIA_PROCEDURE_Q = (
    Q(procedure__categoria__iexact='soroterapia')
    | Q(procedure__categoria__icontains='soroterapia')
    | Q(procedure__categoria__iexact='injetavel')
    | Q(procedure__categoria__icontains='injetavel')
)

SOROTERAPIA_CADASTRO_Q = (
    Q(categoria__iexact='soroterapia')
    | Q(categoria__icontains='soroterapia')
    | Q(categoria__iexact='injetavel')
    | Q(categoria__icontains='injetavel')
)


def _parse_dashboard_period(request, today: date):
    """Intervalo do filtro mensal (mes/ano). No mês atual, termina em today."""
    try:
        ano = int(request.query_params.get('ano') or today.year)
        mes = int(request.query_params.get('mes') or today.month)
        if not (1 <= mes <= 12):
            raise ValueError('mes invalido')
    except (ValueError, TypeError):
        ano, mes = today.year, today.month

    first_day = date(ano, mes, 1)
    last_day = date(ano, mes, calendar.monthrange(ano, mes)[1])
    if ano == today.year and mes == today.month:
        period_end = today
    else:
        period_end = last_day

    return first_day, period_end, mes, ano


def _revenue_by_day(first_day: date, period_end: date):
    """Faturamento por dia usando agregação SQL (uma query em vez de N)."""
    from django.db.models.functions import TruncDay

    rows_db = (
        Payment.objects
        .filter(status='PAID', payment_date__date__gte=first_day, payment_date__date__lte=period_end)
        .annotate(day=TruncDay('payment_date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    revenue_map = {row['day'].date(): float(row['total']) for row in rows_db}

    rows = []
    day = first_day
    while day <= period_end:
        rows.append({'day': day.strftime('%d/%m'), 'value': revenue_map.get(day, 0)})
        day += timedelta(days=1)
    return rows


def _backfill_consultas_data_fim():
    """Consultas concluídas sem data_fim (legado) — usa updated_at para o dashboard."""
    Consulta.objects.filter(status='COMPLETED', data_fim__isnull=True).update(data_fim=F('updated_at'))


def _consulta_realizada_no_periodo_q(period_start, period_end):
    """Consulta concluída no intervalo se data_fim, updated_at ou agendamento cair nele."""

    def in_period(prefix: str) -> Q:
        return (
            Q(**{f'{prefix}__date__gte': period_start})
            & Q(**{f'{prefix}__date__lte': period_end})
        )

    return (
        in_period('data_fim')
        | in_period('updated_at')
        | in_period('appointment__date')
    )


def _consultas_concluidas_no_periodo(period_start, period_end):
    return Consulta.objects.filter(status='COMPLETED').filter(
        _consulta_realizada_no_periodo_q(period_start, period_end),
    )


def _top_procedures_realizados_periodo(period_start, period_end):
    rows = (
        _consultas_concluidas_no_periodo(period_start, period_end)
        .filter(procedure__isnull=False)
        .values('procedure__nome')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    return [
        {'name': item['procedure__nome'] or 'Consulta', 'count': item['count']}
        for item in rows
    ]


def _top_soroterapia_periodo(period_start, period_end):
    """
    Top soroterapias no mês: consultas concluídas + agendamentos (volume).
    Se não houver movimento, lista cadastros ativos de soroterapia (count=0).
    """
    counts: dict[str, int] = {}

    def add_rows(rows):
        for item in rows:
            name = item['procedure__nome'] or 'Sem nome'
            counts[name] = counts.get(name, 0) + item['count']

    add_rows(
        _consultas_concluidas_no_periodo(period_start, period_end)
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values('procedure__nome')
        .annotate(count=Count('id'))
    )
    add_rows(
        Appointment.objects.filter(
            date__date__gte=period_start,
            date__date__lte=period_end,
            status__in=['COMPLETED', 'CONFIRMED', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED', 'SCHEDULED', 'IN_PROGRESS'],
        )
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values('procedure__nome')
        .annotate(count=Count('id'))
    )
    add_rows(
        AppointmentProcedure.objects.filter(
            appointment__date__date__gte=period_start,
            appointment__date__date__lte=period_end,
            appointment__status__in=['COMPLETED', 'CONFIRMED', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED', 'SCHEDULED', 'IN_PROGRESS'],
        )
        .filter(SOROTERAPIA_PROCEDURE_Q)
        .values('procedure__nome')
        .annotate(count=Count('id'))
    )

    ranked = sorted(
        [{'name': name, 'count': count} for name, count in counts.items() if count > 0],
        key=lambda x: x['count'],
        reverse=True,
    )[:5]

    if ranked:
        return ranked

    cadastros = (
        Procedure.objects.filter(is_active=True)
        .filter(SOROTERAPIA_CADASTRO_Q)
        .order_by('nome')
        .values_list('nome', flat=True)[:5]
    )
    return [{'name': nome, 'count': 0} for nome in cadastros]


class LojaInfoView(APIView):
    """GET /clinica-beleza/loja-info/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(info)


class DashboardView(APIView):
    """GET /clinica-beleza/dashboard/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = now().date()
        current = now()
        period_start, period_end, filter_mes, filter_ano = _parse_dashboard_period(request, today)
        period = (request.query_params.get('period') or 'proximos').strip().lower()
        professional_id = request.query_params.get('professional')

        cache_key = (
            f'clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{filter_ano}_{filter_mes:02d}'
            f'_{period}_{professional_id or "all"}'
        )
        skip_cache = (request.query_params.get('refresh') or '').strip().lower() in ('1', 'true', 'yes')
        if not skip_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

        _backfill_consultas_data_fim()

        filter_label = f'{MESES_PT[filter_mes]}/{filter_ano}'
        is_current_month = filter_ano == today.year and filter_mes == today.month

        data = {
            'filter': {
                'mes': filter_mes,
                'ano': filter_ano,
                'label': filter_label,
                'is_current_month': is_current_month,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
            },
            'statistics': self._build_statistics(today, period_start, period_end),
            'next_appointments': self._build_next_appointments(period, professional_id, today, current),
            'revenue_last_7_days': _revenue_by_day(period_start, period_end),
            'top_procedures': _top_procedures_realizados_periodo(period_start, period_end),
            'top_procedures_volume': _top_soroterapia_periodo(period_start, period_end),
        }

        cache.set(cache_key, data, 120)
        return Response(data)

    def _build_statistics(self, today, period_start, period_end):
        """Agrega métricas numéricas do dashboard para o período."""
        yesterday = today - timedelta(days=1)
        revenue_month = Payment.objects.filter(
            status='PAID',
            payment_date__date__gte=period_start,
            payment_date__date__lte=period_end,
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_today = Payment.objects.filter(
            status='PAID', payment_date__date=today,
        ).aggregate(total=Sum('amount'))['total'] or 0
        return {
            'appointments_today': Appointment.objects.filter(date__date=today).count(),
            'appointments_yesterday': Appointment.objects.filter(date__date=yesterday).count(),
            'patients_total': Patient.objects.filter(is_active=True).count(),
            'procedures_total': Procedure.objects.filter(is_active=True).count(),
            'revenue_month': float(revenue_month),
            'revenue_today': float(revenue_today),
            'sessions_month': _consultas_concluidas_no_periodo(period_start, period_end).count(),
        }

    def _build_next_appointments(self, period, professional_id, today, current):
        """Retorna lista serializada dos próximos agendamentos conforme período."""
        if period == 'hoje':
            next_qs = Appointment.objects.filter(date__date=today, date__gte=current)
            limit = 10
        else:
            days_ahead = 7 if period == 'semana' else 14
            horizon = today + timedelta(days=days_ahead)
            next_qs = Appointment.objects.filter(date__gte=current, date__date__lte=horizon)
            limit = 15

        next_qs = next_qs.filter(
            status__in=['SCHEDULED', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED', 'CONFIRMED', 'IN_PROGRESS'],
        ).select_related('patient', 'professional', 'procedure').order_by('date')

        if professional_id:
            try:
                next_qs = next_qs.filter(professional_id=int(professional_id))
            except (ValueError, TypeError):
                pass

        return AppointmentListSerializer(next_qs[:limit], many=True).data
