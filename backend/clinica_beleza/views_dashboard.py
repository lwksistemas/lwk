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
        loja_id = get_current_loja_id()
        today = now().date()

        period = (request.query_params.get('period') or 'hoje').strip().lower()
        professional_id = request.query_params.get('professional')
        cache_key = f'clinica_beleza_dashboard_{loja_id}_{today}_{period}_{professional_id or "all"}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        appointments_today = Appointment.objects.filter(date__date=today).count()
        patients_total = Patient.objects.filter(is_active=True).count()
        procedures_total = Procedure.objects.filter(is_active=True).count()

        first_day_month = today.replace(day=1)
        revenue_month = Payment.objects.filter(
            status='PAID', payment_date__gte=first_day_month, payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0

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
                'patients_total': patients_total,
                'procedures_total': procedures_total,
                'revenue_month': float(revenue_month),
            },
            'next_appointments': AppointmentListSerializer(next_appointments[:limit], many=True).data,
        }

        cache.set(cache_key, data, 300)
        return Response(data)
