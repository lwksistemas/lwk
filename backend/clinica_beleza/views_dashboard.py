"""
Views de Dashboard e Info da Loja — Clínica da Beleza
"""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Patient, Procedure, Appointment, Payment
from .serializers import AppointmentListSerializer
from .utils import LojaContextHelper
from tenants.middleware import get_current_loja_id


# Palavras-chave alinhadas ao frontend (clinica-beleza-categories.ts)
SOROTERAPIA_CATEGORIA_Q = (
    Q(procedure__categoria__icontains='soroterapia')
    | Q(procedure__categoria__icontains='soro')
    | Q(procedure__categoria__icontains='iv ')
    | Q(procedure__categoria__icontains='vitamina')
    | Q(procedure__categoria__icontains='imunidade')
    | Q(procedure__categoria__icontains='detox')
    | Q(procedure__categoria__icontains='disposicao')
)


def _top_procedures_qs(*, first_day_month, today, soroterapia_only: bool, completed_only: bool):
    status_filter = ['COMPLETED'] if completed_only else ['COMPLETED', 'CONFIRMED', 'SCHEDULED', 'IN_PROGRESS']
    qs = Appointment.objects.filter(
        date__date__gte=first_day_month,
        date__date__lte=today,
        status__in=status_filter,
    )
    if soroterapia_only:
        qs = qs.filter(SOROTERAPIA_CATEGORIA_Q)
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
        cache_key = f'clinica_beleza_dashboard_v3_{loja_id}_{today}_{period}_{professional_id or "all"}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

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

        sessions_month = Appointment.objects.filter(
            date__date__gte=first_day_month,
            date__date__lte=today,
            status='COMPLETED',
        ).count()

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

        # Procedimentos realizados no mês (concluídos, todas as categorias)
        top_procedures = _top_procedures_qs(
            first_day_month=first_day_month,
            today=today,
            soroterapia_only=False,
            completed_only=True,
        )
        # Gráfico pizza: volume soroterapia no mês (inclui agendados/confirmados)
        top_procedures_volume = _top_procedures_qs(
            first_day_month=first_day_month,
            today=today,
            soroterapia_only=True,
            completed_only=False,
        )
        if not top_procedures_volume:
            top_procedures_volume = _top_procedures_qs(
                first_day_month=first_day_month,
                today=today,
                soroterapia_only=False,
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
