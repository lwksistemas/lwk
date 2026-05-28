"""
Views de Dashboard e Info da Loja — Clínica da Beleza
"""
from datetime import timedelta
from django.core.cache import cache
from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Patient, Professional, Procedure, Appointment, Payment
from .serializers import AppointmentListSerializer
from .utils import LojaContextHelper
from tenants.middleware import get_current_loja_id


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
        from django.db.models import Count

        loja_id = get_current_loja_id()
        today = now().date()
        yesterday = today - timedelta(days=1)

        period = (request.query_params.get('period') or 'hoje').strip().lower()
        professional_id = request.query_params.get('professional')
        cache_key = f'clinica_beleza_dashboard_{loja_id}_{today}_{period}_{professional_id or "all"}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Estatísticas básicas
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

        # Sessões realizadas no mês (agendamentos concluídos)
        sessions_month = Appointment.objects.filter(
            date__date__gte=first_day_month, date__date__lte=today,
            status='COMPLETED',
        ).count()

        # Faturamento últimos 7 dias
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

        # Top 5 procedimentos mais realizados no mês
        top_procedures_qs = (
            Appointment.objects.filter(
                date__date__gte=first_day_month, date__date__lte=today,
                status__in=['COMPLETED', 'CONFIRMED', 'SCHEDULED'],
            )
            .values('procedure__nome')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        top_procedures = [
            {'name': item['procedure__nome'] or 'Sem nome', 'count': item['count']}
            for item in top_procedures_qs
        ]

        # Próximos agendamentos
        start_date = today
        end_date = today if period == 'hoje' else today + timedelta(days=6)
        limit = 30 if period == 'hoje' else 50

        next_appointments = Appointment.objects.filter(
            date__date__gte=start_date, date__date__lte=end_date,
            status__in=['SCHEDULED', 'CONFIRMED'],
        ).select_related('patient', 'professional', 'procedure').order_by('date')

        if professional_id:
            try:
                next_appointments = next_appointments.filter(professional_id=int(professional_id))
            except (ValueError, TypeError):
                pass

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
            'next_appointments': AppointmentListSerializer(next_appointments[:limit], many=True).data,
            'revenue_last_7_days': revenue_last_7_days,
            'top_procedures': top_procedures,
        }

        cache.set(cache_key, data, 300)
        return Response(data)
