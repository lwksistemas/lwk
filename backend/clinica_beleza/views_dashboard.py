"""
Views de Dashboard e Info da Loja — Clínica da Beleza
"""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, F, Q, Sum
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Patient, Procedure, Appointment, Payment, Consulta
from .serializers import AppointmentListSerializer
from .utils import LojaContextHelper
from tenants.middleware import get_current_loja_id


# Soroterapia: categoria/procedimento do módulo (alinhado ao frontend)
SOROTERAPIA_CATEGORIA_Q = (
    Q(procedure__categoria__iexact='soroterapia')
    | Q(procedure__categoria__icontains='soroterapia')
    | Q(procedure__categoria__icontains='soro')
    | Q(procedure__categoria__icontains='iv ')
    | Q(procedure__categoria__icontains='vitamina')
    | Q(procedure__categoria__icontains='imunidade')
    | Q(procedure__categoria__icontains='detox')
    | Q(procedure__categoria__icontains='disposicao')
)

# Exclui categorias de estética/facial que não são soroterapia
NAO_SOROTERAPIA_CATEGORIA_Q = (
    Q(procedure__categoria__icontains='estetica')
    | Q(procedure__categoria__icontains='estética')
    | Q(procedure__categoria__icontains='facial')
    | Q(procedure__categoria__icontains='corporal')
    | Q(procedure__categoria__icontains='capilar')
    | Q(procedure__categoria__icontains='peeling')
    | Q(procedure__categoria__icontains='botox')
    | Q(procedure__categoria__icontains='preenchimento')
)


def _backfill_consultas_data_fim():
    """Consultas concluídas sem data_fim (legado) — usa updated_at para o dashboard."""
    Consulta.objects.filter(status='COMPLETED', data_fim__isnull=True).update(data_fim=F('updated_at'))


def _consulta_realizada_no_mes_q(first_day_month, today):
    """Consulta concluída no mês se data_fim, updated_at ou agendamento cair no intervalo."""
    def in_month(prefix: str) -> Q:
        return Q(**{f'{prefix}__date__gte': first_day_month}) & Q(**{f'{prefix}__date__lte': today})

    return (
        in_month('data_fim')
        | in_month('updated_at')
        | in_month('appointment__date')
    )


def _consultas_concluidas_no_mes(first_day_month, today):
    return Consulta.objects.filter(status='COMPLETED').filter(
        _consulta_realizada_no_mes_q(first_day_month, today),
    )


def _top_procedures_realizados_mes(first_day_month, today):
    rows = (
        _consultas_concluidas_no_mes(first_day_month, today)
        .values('procedure__nome')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    return [
        {'name': item['procedure__nome'] or 'Sem nome', 'count': item['count']}
        for item in rows
    ]


def _top_procedures_qs(*, first_day_month, today, soroterapia_only: bool, completed_only: bool):
    status_filter = ['COMPLETED'] if completed_only else ['COMPLETED', 'CONFIRMED', 'SCHEDULED', 'IN_PROGRESS']
    qs = Appointment.objects.filter(
        date__date__gte=first_day_month,
        date__date__lte=today,
        status__in=status_filter,
    )
    if soroterapia_only:
        qs = qs.filter(SOROTERAPIA_CATEGORIA_Q).exclude(NAO_SOROTERAPIA_CATEGORIA_Q)
    rows = (
        qs.values('procedure__nome')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    return [
        {'name': item['procedure__nome'] or 'Sem nome', 'count': item['count']}
        for item in rows
    ]


class LojaInfoView(APIView):
    """GET /clinica-beleza/loja-info/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(info)


class DashboardView(APIView):
    """GET /clinica-beleza/dashboard/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = now().date()
        yesterday = today - timedelta(days=1)
        current = now()

        period = (request.query_params.get('period') or 'proximos').strip().lower()
        professional_id = request.query_params.get('professional')
        cache_key = f'clinica_beleza_dashboard_v6_{loja_id}_{today}_{period}_{professional_id or "all"}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        _backfill_consultas_data_fim()

        appointments_today = Appointment.objects.filter(date__date=today).count()
        appointments_yesterday = Appointment.objects.filter(date__date=yesterday).count()
        patients_total = Patient.objects.filter(is_active=True).count()
        procedures_total = Procedure.objects.filter(is_active=True).count()

        first_day_month = today.replace(day=1)
        revenue_month = Payment.objects.filter(
            status='PAID', payment_date__gte=first_day_month, payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        revenue_today = Payment.objects.filter(
            status='PAID', payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        sessions_month = _consultas_concluidas_no_mes(first_day_month, today).count()

        revenue_last_7_days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_revenue = Payment.objects.filter(
                status='PAID', payment_date__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_last_7_days.append({
                'day': day.strftime('%d/%m'),
                'value': float(day_revenue),
            })

        # Procedimentos realizados no mês — consultas concluídas (não data do agendamento)
        top_procedures = _top_procedures_realizados_mes(first_day_month, today)
        # Gráfico pizza: somente soroterapia (sem fallback para outros procedimentos)
        top_procedures_volume = _top_procedures_qs(
            first_day_month=first_day_month,
            today=today,
            soroterapia_only=True,
            completed_only=False,
        )

        # Próximos agendamentos: a partir de agora (não só hoje)
        if period == 'hoje':
            horizon_date = today
            next_qs = Appointment.objects.filter(
                date__date=today,
                date__gte=current,
            )
        else:
            days_ahead = 7 if period == 'semana' else 14
            horizon_date = today + timedelta(days=days_ahead)
            next_qs = Appointment.objects.filter(
                date__gte=current,
                date__date__lte=horizon_date,
            )

        next_qs = next_qs.filter(
            status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
        ).select_related('patient', 'professional', 'procedure').order_by('date')

        if professional_id:
            try:
                next_qs = next_qs.filter(professional_id=int(professional_id))
            except (ValueError, TypeError):
                pass

        limit = 10 if period == 'hoje' else 15

        data = {
            'statistics': {
                'appointments_today': appointments_today,
                'appointments_yesterday': appointments_yesterday,
                'patients_total': patients_total,
                'procedures_total': procedures_total,
                'revenue_month': float(revenue_month),
                'revenue_today': float(revenue_today),
                'sessions_month': sessions_month,
            },
            'next_appointments': AppointmentListSerializer(next_qs[:limit], many=True).data,
            'revenue_last_7_days': revenue_last_7_days,
            'top_procedures': top_procedures,
            'top_procedures_volume': top_procedures_volume,
        }

        cache.set(cache_key, data, 300)
        return Response(data)
