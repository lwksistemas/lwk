"""
Views/API para Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Count, Sum, Q
from datetime import timedelta
from .models import Patient, Professional, Procedure, Appointment, Payment
from .serializers import (
    PatientSerializer, ProfessionalSerializer, ProcedureSerializer,
    AppointmentListSerializer, AppointmentDetailSerializer, AppointmentCreateSerializer,
    PaymentSerializer
)


class DashboardView(APIView):
    """
    Dashboard principal com estatísticas
    GET /clinica-beleza/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        
        # Estatísticas do dia
        appointments_today = Appointment.objects.filter(date__date=today).count()
        
        # Total de pacientes ativos
        patients_total = Patient.objects.filter(active=True).count()
        
        # Total de procedimentos ativos
        procedures_total = Procedure.objects.filter(active=True).count()
        
        # Faturamento do mês
        first_day_month = today.replace(day=1)
        revenue_month = Payment.objects.filter(
            status='PAID',
            payment_date__gte=first_day_month,
            payment_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Próximos agendamentos (hoje)
        next_appointments = Appointment.objects.filter(
            date__date=today,
            status__in=['SCHEDULED', 'CONFIRMED']
        ).select_related('patient', 'professional', 'procedure').order_by('date')[:5]
        
        return Response({
            'statistics': {
                'appointments_today': appointments_today,
                'patients_total': patients_total,
                'procedures_total': procedures_total,
                'revenue_month': float(revenue_month)
            },
            'next_appointments': AppointmentListSerializer(next_appointments, many=True).data
        })


class AppointmentListView(APIView):
    """
    Listagem e criação de agendamentos
    GET /clinica-beleza/appointments/
    POST /clinica-beleza/appointments/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtros opcionais
        date_filter = request.query_params.get('date')
        status_filter = request.query_params.get('status')
        professional_filter = request.query_params.get('professional')
        
        queryset = Appointment.objects.select_related('patient', 'professional', 'procedure')
        
        if date_filter:
            queryset = queryset.filter(date__date=date_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if professional_filter:
            queryset = queryset.filter(professional_id=professional_filter)
        
        queryset = queryset.order_by('-date')
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentDetailView(APIView):
    """
    Detalhes, atualização e exclusão de agendamento
    GET /clinica-beleza/appointments/<id>/
    PUT /clinica-beleza/appointments/<id>/
    DELETE /clinica-beleza/appointments/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            appointment = Appointment.objects.select_related('patient', 'professional', 'procedure').get(pk=pk)
            serializer = AppointmentDetailSerializer(appointment)
            return Response(serializer.data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            serializer = AppointmentCreateSerializer(appointment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            appointment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class PatientListView(APIView):
    """
    Listagem e criação de pacientes
    GET /clinica-beleza/patients/
    POST /clinica-beleza/patients/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patients = Patient.objects.filter(active=True).order_by('name')
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalListView(APIView):
    """
    Listagem e criação de profissionais
    GET /clinica-beleza/professionals/
    POST /clinica-beleza/professionals/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professionals = Professional.objects.filter(active=True).order_by('name')
        serializer = ProfessionalSerializer(professionals, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProfessionalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureListView(APIView):
    """
    Listagem e criação de procedimentos
    GET /clinica-beleza/procedures/
    POST /clinica-beleza/procedures/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        procedures = Procedure.objects.filter(active=True).order_by('name')
        serializer = ProcedureSerializer(procedures, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProcedureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentListView(APIView):
    """
    Listagem e criação de pagamentos
    GET /clinica-beleza/payments/
    POST /clinica-beleza/payments/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.select_related('appointment').order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
