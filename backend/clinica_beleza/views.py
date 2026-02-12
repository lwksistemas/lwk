"""
Views/API para Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Count, Q, Sum
from datetime import timedelta
from .models import Patient, Professional, Procedure, Appointment, Payment, BloqueioHorario
from .serializers import (
    PatientSerializer, ProfessionalSerializer, ProcedureSerializer,
    AppointmentListSerializer, AppointmentDetailSerializer, AppointmentCreateSerializer,
    PaymentSerializer, AgendaEventSerializer, BloqueioHorarioSerializer
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
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Patient.objects.all().order_by('name')
        if active_only:
            queryset = queryset.filter(active=True)
        serializer = PatientSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetailView(APIView):
    """GET /clinica-beleza/patients/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Patient.objects.get(pk=pk)
            return Response(PatientSerializer(obj).data)
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Patient.objects.get(pk=pk)
            serializer = PatientSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = Patient.objects.get(pk=pk)
            obj.active = False
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ProfessionalListView(APIView):
    """
    Listagem e criação de profissionais
    GET /clinica-beleza/professionals/
    POST /clinica-beleza/professionals/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Professional.objects.all().order_by('name')
        if active_only:
            queryset = queryset.filter(active=True)
        serializer = ProfessionalSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProfessionalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            return Response(ProfessionalSerializer(obj).data)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            serializer = ProfessionalSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            obj.active = False
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ProcedureListView(APIView):
    """
    Listagem e criação de procedimentos
    GET /clinica-beleza/procedures/
    POST /clinica-beleza/procedures/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Procedure.objects.all().order_by('name')
        if active_only:
            queryset = queryset.filter(active=True)
        serializer = ProcedureSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProcedureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureDetailView(APIView):
    """GET /clinica-beleza/procedures/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Procedure.objects.get(pk=pk)
            return Response(ProcedureSerializer(obj).data)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Procedure.objects.get(pk=pk)
            serializer = ProcedureSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = Procedure.objects.get(pk=pk)
            obj.active = False
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class PaymentListView(APIView):
    """
    Listagem e criação de pagamentos (financeiro da clínica)
    GET /clinica-beleza/payments/?status=PAID&date=2024-01-15&professional=1
    POST /clinica-beleza/payments/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Payment.objects.select_related(
            'appointment', 'appointment__patient', 'appointment__professional', 'appointment__procedure'
        ).order_by('-created_at')
        status_filter = request.query_params.get('status')
        date_filter = request.query_params.get('date')
        professional_id = request.query_params.get('professional')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_filter:
            queryset = queryset.filter(payment_date__date=date_filter)
        if professional_id:
            queryset = queryset.filter(appointment__professional_id=professional_id)
        serializer = PaymentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(APIView):
    """
    Detalhe, atualização e exclusão de pagamento
    GET /clinica-beleza/payments/<id>/
    PUT /clinica-beleza/payments/<id>/
    DELETE /clinica-beleza/payments/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            payment = Payment.objects.select_related(
                'appointment', 'appointment__patient', 'appointment__professional', 'appointment__procedure'
            ).get(pk=pk)
            serializer = PaymentSerializer(payment)
            return Response(serializer.data)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            serializer = PaymentSerializer(payment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            payment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Payment.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class FinanceiroResumoView(APIView):
    """
    Resumo financeiro: caixa diário, total mês, contas a receber
    GET /clinica-beleza/financeiro/resumo/?mes=2024-01
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        first_day_month = today.replace(day=1)
        # Caixa diário: total pago hoje
        caixa_diario = Payment.objects.filter(
            status='PAID',
            payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        # Total do mês (pago)
        total_mes = Payment.objects.filter(
            status='PAID',
            payment_date__date__gte=first_day_month,
            payment_date__date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        # Contas a receber (pendente)
        contas_a_receber = Payment.objects.filter(
            status='PENDING'
        ).aggregate(total=Sum('amount'))['total'] or 0
        # Total comissões do mês (pagos)
        comissao_mes = Payment.objects.filter(
            status='PAID',
            payment_date__date__gte=first_day_month,
            payment_date__date__lte=today
        ).aggregate(total=Sum('comissao_valor'))['total'] or 0
        return Response({
            'caixa_diario': float(caixa_diario),
            'total_mes': float(total_mes),
            'contas_a_receber': float(contas_a_receber),
            'comissao_mes': float(comissao_mes),
        })


class AgendaView(APIView):
    """
    Agenda/Calendário - Retorna eventos no formato FullCalendar
    GET /clinica-beleza/agenda/
    Parâmetros:
    - start: data inicial (YYYY-MM-DD)
    - end: data final (YYYY-MM-DD)
    - professional: ID do profissional (opcional)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtros
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        professional_id = request.query_params.get('professional')
        
        queryset = Appointment.objects.select_related('patient', 'professional', 'procedure')
        
        # Filtrar por período
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filtrar por profissional
        if professional_id:
            queryset = queryset.filter(professional_id=professional_id)
        
        # Excluir cancelados (opcional)
        # queryset = queryset.exclude(status='CANCELLED')
        
        queryset = queryset.order_by('date')
        
        serializer = AgendaEventSerializer(queryset, many=True)
        return Response(serializer.data)


class AgendaUpdateView(APIView):
    """
    Atualizar data/hora do agendamento (drag & drop).
    Respeita bloqueios: não permite soltar em horário bloqueado.
    PATCH /clinica-beleza/agenda/<id>/update/
    Body: { "date": "2024-02-11T14:30:00Z" }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.select_related('procedure', 'professional').get(pk=pk)
            new_date = request.data.get('date')
            if not new_date:
                return Response({'error': 'Data não fornecida'}, status=status.HTTP_400_BAD_REQUEST)

            if hasattr(new_date, 'isoformat'):
                date_start = new_date
            elif isinstance(new_date, str):
                from django.utils.dateparse import parse_datetime
                date_start = parse_datetime(new_date) or now()
            else:
                date_start = new_date

            date_end = date_start + timedelta(minutes=appointment.procedure.duration)
            professional_id = appointment.professional_id
            bloqueios = BloqueioHorario.objects.filter(
                Q(professional_id=professional_id) | Q(professional_id__isnull=True)
            )
            if _bloqueio_impede_agendamento(date_start, date_end, professional_id, bloqueios):
                return Response(
                    {'error': 'Horário bloqueado. Escolha outro horário.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            appointment.date = date_start
            appointment.save()

            serializer = AgendaEventSerializer(appointment)
            return Response(serializer.data)

        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class AgendaCreateView(APIView):
    """
    Criar novo agendamento pela agenda
    POST /clinica-beleza/agenda/create/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            date_start = data['date']
            # Fim = início + duração do procedimento
            from datetime import timedelta
            date_end = date_start + timedelta(minutes=data['procedure'].duration)
            professional_id = data['professional'].id
            bloqueios = BloqueioHorario.objects.filter(
                Q(professional_id=professional_id) | Q(professional_id__isnull=True)
            )
            if _bloqueio_impede_agendamento(date_start, date_end, professional_id, bloqueios):
                return Response(
                    {'error': 'Horário bloqueado. Escolha outro horário ou profissional.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            appointment = serializer.save()
            event_serializer = AgendaEventSerializer(appointment)
            return Response(event_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgendaDeleteView(APIView):
    """
    Deletar agendamento
    DELETE /clinica-beleza/agenda/<id>/delete/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            appointment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Bloqueio de Horários (almoço, férias, manutenção, evento)
# ---------------------------------------------------------------------------

def _bloqueio_impede_agendamento(data_inicio, data_fim, professional_id, bloqueios_queryset):
    """Verifica se algum bloqueio impede o agendamento no intervalo [data_inicio, data_fim] para o profissional."""
    for b in bloqueios_queryset:
        # Bloqueio geral (sem profissional) ou do mesmo profissional
        if b.professional_id is None or b.professional_id == professional_id:
            # Conflito se os intervalos se sobrepõem
            if data_inicio < b.data_fim and data_fim > b.data_inicio:
                return True
    return False


class BloqueioHorarioListView(APIView):
    """
    Listar e criar bloqueios de horário
    GET /clinica-beleza/bloqueios/?start=YYYY-MM-DD&end=YYYY-MM-DD&professional=<id>
    POST /clinica-beleza/bloqueios/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        professional_id = request.query_params.get('professional')
        queryset = BloqueioHorario.objects.all().select_related('professional').order_by('-data_inicio')
        if start:
            queryset = queryset.filter(data_fim__gte=start)
        if end:
            queryset = queryset.filter(data_inicio__lte=end)
        if professional_id:
            queryset = queryset.filter(
                Q(professional_id=professional_id) | Q(professional_id__isnull=True)
            )
        serializer = BloqueioHorarioSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BloqueioHorarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BloqueioHorarioDetailView(APIView):
    """
    Detalhar, atualizar e excluir bloqueio
    GET /clinica-beleza/bloqueios/<id>/
    PUT /clinica-beleza/bloqueios/<id>/
    DELETE /clinica-beleza/bloqueios/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = BloqueioHorario.objects.select_related('professional').get(pk=pk)
            serializer = BloqueioHorarioSerializer(obj)
            return Response(serializer.data)
        except BloqueioHorario.DoesNotExist:
            return Response({'error': 'Bloqueio não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = BloqueioHorario.objects.get(pk=pk)
            serializer = BloqueioHorarioSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BloqueioHorario.DoesNotExist:
            return Response({'error': 'Bloqueio não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = BloqueioHorario.objects.get(pk=pk)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BloqueioHorario.DoesNotExist:
            return Response({'error': 'Bloqueio não encontrado'}, status=status.HTTP_404_NOT_FOUND)

