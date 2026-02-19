"""
Views/API para Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.timezone import now
from django.db.models import Count, Q, Sum
from django.core.exceptions import ValidationError
from django.core.cache import cache
from datetime import timedelta, date
from .models import Patient, Professional, Procedure, Appointment, Payment, BloqueioHorario, CampanhaPromocao, HorarioTrabalhoProfissional
from rules.base import MotorRegras
from .serializers import (
    PatientSerializer, ProfessionalSerializer, ProfessionalCreateWithUserSerializer,
    ProcedureSerializer,
    AppointmentListSerializer, AppointmentDetailSerializer, AppointmentCreateSerializer,
    PaymentSerializer, AgendaEventSerializer, BloqueioHorarioSerializer,
    HorarioTrabalhoProfissionalSerializer,
)
from tenants.middleware import get_current_loja_id
from .utils import LojaContextHelper


class LojaInfoView(APIView):
    """
    Informações da loja atual (administrador) para exibir na interface.
    GET /clinica-beleza/loja-info/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = LojaContextHelper.get_loja_owner_info()
        if info is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(info)


class DashboardView(APIView):
    """
    Dashboard principal com estatísticas
    GET /clinica-beleza/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        loja_id = get_current_loja_id()
        today = now().date()
        
        # Filtros para cache key
        period = (request.query_params.get('period') or 'hoje').strip().lower()
        professional_id = request.query_params.get('professional')
        cache_key = f'clinica_beleza_dashboard_{loja_id}_{today}_{period}_{professional_id or "all"}'
        
        # Tentar buscar do cache (5 minutos)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
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
        
        # Próximos Atendimentos
        start_date = today
        end_date = today if period == 'hoje' else today + timedelta(days=6)
        limit = 30 if period == 'hoje' else 50
        
        next_appointments = Appointment.objects.filter(
            date__date__gte=start_date,
            date__date__lte=end_date,
            status__in=['SCHEDULED', 'CONFIRMED']
        ).select_related('patient', 'professional', 'procedure').order_by('date')
        
        if professional_id:
            try:
                next_appointments = next_appointments.filter(professional_id=int(professional_id))
            except (ValueError, TypeError):
                pass
        
        next_appointments = next_appointments[:limit]
        
        data = {
            'statistics': {
                'appointments_today': appointments_today,
                'patients_total': patients_total,
                'procedures_total': procedures_total,
                'revenue_month': float(revenue_month)
            },
            'next_appointments': AppointmentListSerializer(next_appointments, many=True).data
        }
        
        # Salvar no cache por 5 minutos
        cache.set(cache_key, data, 300)
        
        return Response(data)


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
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        serializer = ProfessionalSerializer(
            queryset, many=True,
            context={'owner_professional_id': owner_professional_id}
        )
        return Response(serializer.data)

    def post(self, request):
        import logging
        import json
        log = logging.getLogger(__name__)
        raw = request.data
        if not isinstance(raw, dict) and hasattr(raw, 'items'):
            raw = dict(raw)
        if not isinstance(raw, dict):
            raw = {}
        log.warning('POST professionals raw keys=%s', list(raw.keys()))

        def _empty_to_none(v):
            if v is None:
                return None
            if isinstance(v, list):
                v = v[0] if len(v) == 1 else None
            if v is None:
                return None
            if isinstance(v, str) and (v.strip() == '' or v.strip().lower() == 'null'):
                return None
            return v

        data = {}
        for k, v in raw.items():
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            data[k] = v

        for key in ('email', 'phone'):
            if key in data:
                data[key] = _empty_to_none(data[key])

        # name/specialty: strip e não enviar string vazia (evita "blank" no serializer)
        for key in ('name', 'specialty'):
            if key in data and isinstance(data[key], str):
                data[key] = (data[key] or '').strip() or None

        criar_acesso = data.get('criar_acesso') and data.get('email')
        if criar_acesso:
            serializer = ProfessionalCreateWithUserSerializer(data=data)
            if serializer.is_valid():
                professional = serializer.save()
                return Response(
                    ProfessionalSerializer(professional).data,
                    status=status.HTTP_201_CREATED,
                )
            log.warning('POST professionals (criar_acesso): validation errors %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Validação antecipada para mensagem clara
        def _str_val(key):
            v = data.get(key)
            if isinstance(v, list):
                v = v[0] if v else ''
            return (v or '').strip() if isinstance(v, str) else ''
        name_val = _str_val('name')
        specialty_val = _str_val('specialty')
        if not name_val or not specialty_val:
            missing = []
            if not name_val:
                missing.append('nome')
            if not specialty_val:
                missing.append('especialidade')
            return Response(
                {'detail': f'Preencha {", ".join(missing)}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apenas campos do model Professional; active como booleano
        active_val = data.get('active', True)
        if isinstance(active_val, str):
            active_val = active_val.strip().lower() in ('1', 'true', 'yes', 'on')
        payload = {
            'name': name_val,
            'specialty': specialty_val,
            'phone': data.get('phone'),
            'email': data.get('email'),
            'active': bool(active_val),
        }
        serializer = ProfessionalSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        err_msg = json.dumps(serializer.errors, ensure_ascii=False)
        log.warning('POST professionals 400 payload=%s errors=%s', payload, err_msg)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE. O administrador vinculado à loja não pode ser editado nem excluído."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            owner_professional_id = LojaContextHelper.get_owner_professional_id()
            return Response(ProfessionalSerializer(
                obj, context={'owner_professional_id': owner_professional_id}
            ).data)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response(
                {'error': 'O administrador vinculado à loja não pode ser editado.'},
                status=status.HTTP_403_FORBIDDEN
            )
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
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response(
                {'error': 'O administrador vinculado à loja não pode ser excluído.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            obj = Professional.objects.get(pk=pk)
            
            # Excluir agendamentos futuros deste profissional
            from django.utils import timezone
            agora = timezone.now()
            agendamentos_futuros = Appointment.objects.filter(
                professional=obj,
                date__gte=agora
            )
            count_agendamentos = agendamentos_futuros.count()
            agendamentos_futuros.delete()
            
            # Excluir horários de trabalho
            HorarioTrabalhoProfissional.objects.filter(professional=obj).delete()
            
            # Excluir bloqueios específicos deste profissional
            BloqueioHorario.objects.filter(professional=obj).delete()
            
            # Marcar profissional como inativo
            obj.active = False
            obj.save()
            
            return Response({
                'message': f'Profissional desativado com sucesso. {count_agendamentos} agendamento(s) futuro(s) foram excluídos.'
            }, status=status.HTTP_200_OK)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class HorarioTrabalhoProfissionalView(APIView):
    """
    Dias e horários de trabalho do profissional.
    GET /clinica-beleza/professionals/<id>/horarios-trabalho/  → lista
    PUT /clinica-beleza/professionals/<id>/horarios-trabalho/  → substitui todos (body: lista de { dia_semana, hora_entrada, hora_saida, intervalo_inicio?, intervalo_fim?, ativo? })
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            professional = Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        queryset = HorarioTrabalhoProfissional.objects.filter(professional_id=pk).order_by('dia_semana')
        serializer = HorarioTrabalhoProfissionalSerializer(queryset, many=True)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            professional = Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Envie uma lista de horários. Ex.: [{"dia_semana": 0, "hora_entrada": "08:00", "hora_saida": "18:00", "ativo": true}]'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Remover horários atuais e criar os novos
        HorarioTrabalhoProfissional.objects.filter(professional_id=pk).delete()
        created = []
        for item in request.data:
            item = dict(item)
            serializer = HorarioTrabalhoProfissionalSerializer(data=item)
            if serializer.is_valid():
                obj = serializer.save(professional=professional)
                created.append(HorarioTrabalhoProfissionalSerializer(obj).data)
            else:
                HorarioTrabalhoProfissional.objects.filter(professional_id=pk).delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(created, status=status.HTTP_200_OK)


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


class AgendaHojeView(APIView):
    """
    Agenda do dia (recepção).
    GET /clinica-beleza/agenda/hoje/
    Retorna apenas agendamentos de hoje, ordenados por horário.
    Acesso: qualquer usuário autenticado da loja (admin, recepção, profissional).
    Para restringir só a recepção/admin: use permission_classes = [IsRecepcaoOrAdmin].
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoje = now().date()
        queryset = (
            Appointment.objects
            .select_related('patient', 'professional', 'procedure')
            .filter(date__date=hoje)
            .order_by('date')
        )
        serializer = AgendaEventSerializer(queryset, many=True)
        return Response(serializer.data)


class AgendaUpdateView(APIView):
    """
    Atualizar data/hora e/ou status do agendamento.
    PATCH /clinica-beleza/agenda/<id>/update/
    Body: { "date": "...", "status": "CONFIRMED", "version": 1 }.
    Se version for enviado e for diferente da versão no servidor → 409 Conflict
    com { "conflict": true, "server": {...}, "local": {...} }.
    Para forçar aplicação da versão local (após usuário escolher "Usar minha versão"):
    envie resolve_use_local: true no body.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        import logging
        logger = logging.getLogger(__name__)
        try:
            appointment = Appointment.objects.select_related('procedure', 'professional', 'patient').get(pk=pk)
            new_date = request.data.get('date')
            new_status = request.data.get('status')
            local_version = request.data.get('version')
            resolve_use_local = request.data.get('resolve_use_local') is True

            # Conflito de sincronização: cliente envia version; se diferente do servidor → 409
            if local_version is not None and not resolve_use_local:
                if appointment.version != local_version:
                    logger.info(
                        "Conflito de sincronização agendamento id=%s: servidor version=%s, local version=%s",
                        pk, appointment.version, local_version
                    )
                    server_data = AgendaEventSerializer(appointment).data
                    local_payload = {
                        'id': appointment.id,
                        'version': local_version,
                        'date': request.data.get('date'),
                        'status': request.data.get('status'),
                        'updated_at': request.data.get('updated_at'),
                    }
                    # Regras de prioridade para hint na resolução (frontend pode sugerir ação)
                    resolution_hint = None
                    if appointment.status == 'CANCELLED':
                        resolution_hint = 'server_cancelled'  # Cancelamento sempre vence
                    elif appointment.updated_at and request.data.get('updated_at'):
                        try:
                            from django.utils.dateparse import parse_datetime
                            server_ts = appointment.updated_at
                            local_ts = parse_datetime(request.data.get('updated_at'))
                            if local_ts and server_ts and local_ts > server_ts:
                                resolution_hint = 'local_newer'  # Alteração mais recente vence
                        except Exception:
                            pass
                    return Response(
                        {
                            'conflict': True,
                            'server': server_data,
                            'local': local_payload,
                            'resolution_hint': resolution_hint,
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

            if new_date is not None:
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
                # Motor de regras: conflito de horário (mesmo profissional)
                try:
                    motor = MotorRegras()
                    motor.executar(
                        evento="AGENDAMENTO_ATUALIZADO",
                        contexto={
                            "profissional": appointment.professional,
                            "date": date_start,
                            "date_end": date_end,
                            "appointment_id": appointment.id,
                        },
                    )
                except ValidationError as e:
                    msg = e.messages[0] if getattr(e, "messages", None) else str(e)
                    return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
                appointment.date = date_start

            if new_status is not None:
                valid = dict(Appointment.STATUS_CHOICES).keys()
                if new_status not in valid:
                    return Response(
                        {'error': f'Status inválido. Use: {", ".join(valid)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                appointment.status = new_status

            if new_date is None and new_status is None and not resolve_use_local:
                return Response({'error': 'Envie date e/ou status'}, status=status.HTTP_400_BAD_REQUEST)

            # Versionamento e auditoria
            appointment.version = (appointment.version or 1) + 1
            appointment.updated_by_id = getattr(request.user, 'id', None)
            appointment.save()

            # Motor de regras: ao finalizar atendimento, gera lançamento financeiro (Payment pendente)
            if new_status == 'COMPLETED':
                try:
                    motor = MotorRegras()
                    motor.executar(
                        evento="AGENDAMENTO_FINALIZADO",
                        contexto={"appointment": appointment},
                    )
                except Exception:
                    pass  # não falha a atualização

            # WhatsApp: enviar confirmação quando status passar a CONFIRMED (respeita config da loja)
            if new_status == 'CONFIRMED':
                try:
                    if getattr(appointment.patient, 'allow_whatsapp', True):
                        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
                        if config and config.enviar_confirmacao:
                            from whatsapp.services import enviar_confirmacao_agendamento
                            enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
                except Exception as e:
                    logger.warning("WhatsApp confirmação agendamento %s: %s", pk, e)

            logger.info(
                "Agendamento id=%s atualizado: version=%s updated_by_id=%s",
                appointment.id, appointment.version, appointment.updated_by_id
            )
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
        import logging
        logger = logging.getLogger(__name__)
        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            date_start = data['date']
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
            # Motor de regras: validar conflito antes de salvar
            motor = MotorRegras()
            try:
                motor.executar(
                    evento="AGENDAMENTO_CRIADO",
                    contexto={
                        "profissional": data["professional"],
                        "date": date_start,
                        "date_end": date_end,
                        "appointment_id": None,
                    },
                )
            except ValidationError as e:
                msg = e.messages[0] if getattr(e, "messages", None) else str(e)
                return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
            appointment = serializer.save()
            # Regras pós-criação: notificação ao profissional
            try:
                motor.executar(
                    evento="AGENDAMENTO_CRIADO",
                    contexto={
                        "profissional": appointment.professional,
                        "date": appointment.date,
                        "date_end": appointment.date + timedelta(minutes=appointment.procedure.duration),
                        "appointment_id": appointment.id,
                        "appointment": appointment,
                    },
                )
            except Exception:
                pass  # não falha a criação
            # WhatsApp: enviar confirmação ao criar agendamento (status CONFIRMED ou SCHEDULED)
            if appointment.status in ('CONFIRMED', 'SCHEDULED') and getattr(appointment.patient, 'allow_whatsapp', True):
                try:
                    patient_phone = getattr(appointment.patient, 'phone', None) or ''
                    if not (patient_phone and str(patient_phone).strip()):
                        logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — paciente sem telefone", appointment.id)
                    else:
                        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
                        if not config:
                            logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — contexto/config loja ausente", appointment.id)
                        elif not config.enviar_confirmacao:
                            logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — opção desligada nas Configurações", appointment.id)
                        else:
                            from whatsapp.services import enviar_confirmacao_agendamento
                            if enviar_confirmacao_agendamento(appointment, user=request.user, config=config):
                                logger.info("WhatsApp confirmação enviada ao criar agendamento id=%s", appointment.id)
                            else:
                                logger.info(
                                    "WhatsApp: confirmação não enviada ao criar agendamento id=%s — API Meta não configurada.",
                                    appointment.id,
                                )
                except Exception as e:
                    logger.warning("WhatsApp confirmação ao criar agendamento %s: %s", appointment.id, e)
            event_serializer = AgendaEventSerializer(appointment)
            return Response(event_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            msg = e.messages[0] if getattr(e, "messages", None) else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Erro ao criar agendamento: %s", e)
            return Response(
                {'error': 'Erro ao salvar agendamento. Verifique se a loja está configurada e tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


class AgendaReenviarMensagemView(APIView):
    """
    Reenviar mensagem de confirmação WhatsApp ao paciente do agendamento.
    POST /clinica-beleza/agenda/<id>/reenviar-mensagem/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        import logging
        logger = logging.getLogger(__name__)
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if not getattr(appointment.patient, 'allow_whatsapp', True):
            return Response({'sent': False, 'message': 'Paciente não permite receber WhatsApp.'}, status=status.HTTP_200_OK)
        if not (getattr(appointment.patient, 'phone', None) or '').strip():
            return Response({'sent': False, 'message': 'Paciente sem telefone cadastrado.'}, status=status.HTTP_200_OK)
        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not config.enviar_confirmacao:
            return Response({'sent': False, 'message': 'Envio de confirmação desativado nas Configurações.'}, status=status.HTTP_200_OK)
        from whatsapp.services import enviar_confirmacao_agendamento
        try:
            ok = enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
            if ok:
                logger.info("WhatsApp reenvio confirmação agendamento id=%s", pk)
                return Response({'sent': True, 'message': 'Mensagem reenviada com sucesso.'})
            return Response({'sent': False, 'message': 'Não foi possível enviar (verifique a integração WhatsApp nas Configurações).'})
        except Exception as e:
            logger.warning("WhatsApp reenvio agendamento %s: %s", pk, e)
            return Response({'sent': False, 'message': f'Erro ao enviar: {str(e)}'})


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
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Erro ao criar BloqueioHorario: %s", e)
            return Response(
                {'error': 'Erro ao salvar bloqueio. Verifique data/hora e tente novamente.'},
                status=status.HTTP_400_BAD_REQUEST
            )


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


class WhatsAppConfigView(APIView):
    """
    Configuração WhatsApp da loja (ETAPA 4).
    GET /clinica-beleza/whatsapp-config/  → retorna flags
    PATCH /clinica-beleza/whatsapp-config/ → atualiza flags
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        import logging
        logger = logging.getLogger(__name__)
        loja_id = get_current_loja_id()
        if not loja_id and request:
            # Fallback: header pode ter sido enviado mas contexto perdido (ex.: worker async)
            try:
                lid = request.headers.get('X-Loja-ID')
                if lid:
                    loja_id = int(lid)
            except (ValueError, TypeError):
                pass
            if not loja_id:
                slug = (request.headers.get('X-Tenant-Slug') or '').strip()
                if slug:
                    from superadmin.models import Loja
                    loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                    if loja:
                        loja_id = loja.id
        if not loja_id:
            logger.warning("WhatsAppConfigView: contexto de loja não encontrado (loja_id e headers vazios)")
            return None
        from whatsapp.models import WhatsAppConfig
        from superadmin.models import Loja
        try:
            loja = Loja.objects.using('default').get(id=loja_id)
            owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
            # Banco do tenant (cada loja tem sua tabela whatsapp_whatsappconfig no próprio schema)
            config, created = WhatsAppConfig.objects.get_or_create(
                loja=loja,
                defaults={
                    'enviar_confirmacao': True,
                    'enviar_lembrete_24h': True,
                    'enviar_lembrete_2h': True,
                    'enviar_cobranca': True,
                    'whatsapp_numero': owner_tel or '',
                }
            )
            if not created and not (config.whatsapp_numero or '').strip() and owner_tel:
                config.whatsapp_numero = owner_tel
                config.save(update_fields=['whatsapp_numero', 'updated_at'])
            return config
        except Exception as e:
            logger.exception("WhatsAppConfigView._get_config erro loja_id=%s: %s", loja_id, e)
            return None

    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        # API Meta: expor para a clínica configurar no frontend (token nunca retornado em texto)
        return Response({
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (getattr(config, 'whatsapp_phone_id', None) or '').strip(),
            'whatsapp_token_set': bool((getattr(config, 'whatsapp_token', None) or '').strip()),
        })

    def patch(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        update_fields = ['updated_at']
        for key in ('enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca'):
            if key in request.data:
                setattr(config, key, bool(request.data[key]))
                update_fields.append(key)
        if 'whatsapp_numero' in request.data:
            config.whatsapp_numero = (request.data.get('whatsapp_numero') or '').strip()[:20]
            update_fields.append('whatsapp_numero')
        if 'whatsapp_ativo' in request.data:
            config.whatsapp_ativo = bool(request.data['whatsapp_ativo'])
            update_fields.append('whatsapp_ativo')
        if 'whatsapp_phone_id' in request.data:
            config.whatsapp_phone_id = (request.data.get('whatsapp_phone_id') or '').strip()[:64]
            update_fields.append('whatsapp_phone_id')
        if 'whatsapp_token' in request.data:
            config.whatsapp_token = (request.data.get('whatsapp_token') or '').strip()[:512]
            update_fields.append('whatsapp_token')
        config.save(update_fields=update_fields)
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return Response({
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (config.whatsapp_phone_id or '').strip(),
            'whatsapp_token_set': bool((config.whatsapp_token or '').strip()),
        })


# ---------------------------------------------------------------------------
# Campanhas de promoções (envio em massa WhatsApp)
# ---------------------------------------------------------------------------

class CampanhaPromocaoListView(APIView):
    """GET /clinica-beleza/campanhas/  POST /clinica-beleza/campanhas/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        campanhas = CampanhaPromocao.objects.all().order_by('-created_at')
        data = [{
            'id': c.id,
            'titulo': c.titulo,
            'mensagem': c.mensagem,
            'data_inicio': c.data_inicio.isoformat() if c.data_inicio else None,
            'data_fim': c.data_fim.isoformat() if c.data_fim else None,
            'ativa': c.ativa,
            'enviada_em': c.enviada_em.isoformat() if c.enviada_em else None,
            'total_enviados': c.total_enviados,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        } for c in campanhas]
        return Response(data)

    def post(self, request):
        titulo = (request.data.get('titulo') or '').strip()[:200]
        mensagem = (request.data.get('mensagem') or '').strip()
        if not titulo or not mensagem:
            return Response({'error': 'Título e mensagem são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        from django.utils.dateparse import parse_date
        campanha = CampanhaPromocao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            data_inicio=parse_date(data_inicio) if data_inicio else None,
            data_fim=parse_date(data_fim) if data_fim else None,
            ativa=bool(request.data.get('ativa', True)),
        )
        return Response({
            'id': campanha.id,
            'titulo': campanha.titulo,
            'mensagem': campanha.mensagem,
            'data_inicio': campanha.data_inicio.isoformat() if campanha.data_inicio else None,
            'data_fim': campanha.data_fim.isoformat() if campanha.data_fim else None,
            'ativa': campanha.ativa,
            'enviada_em': None,
            'total_enviados': 0,
            'created_at': campanha.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class CampanhaPromocaoDetailView(APIView):
    """GET /clinica-beleza/campanhas/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return CampanhaPromocao.objects.get(pk=pk)

    def get(self, request, pk):
        try:
            c = self.get_object(pk)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'id': c.id, 'titulo': c.titulo, 'mensagem': c.mensagem,
            'data_inicio': c.data_inicio.isoformat() if c.data_inicio else None,
            'data_fim': c.data_fim.isoformat() if c.data_fim else None,
            'ativa': c.ativa,
            'enviada_em': c.enviada_em.isoformat() if c.enviada_em else None,
            'total_enviados': c.total_enviados,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        })

    def put(self, request, pk):
        try:
            c = self.get_object(pk)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        if 'titulo' in request.data:
            c.titulo = (request.data.get('titulo') or '').strip()[:200]
        if 'mensagem' in request.data:
            c.mensagem = (request.data.get('mensagem') or '').strip()
        if 'data_inicio' in request.data:
            from django.utils.dateparse import parse_date
            c.data_inicio = parse_date(request.data['data_inicio']) if request.data.get('data_inicio') else None
        if 'data_fim' in request.data:
            from django.utils.dateparse import parse_date
            c.data_fim = parse_date(request.data['data_fim']) if request.data.get('data_fim') else None
        if 'ativa' in request.data:
            c.ativa = bool(request.data['ativa'])
        c.save()
        return Response({
            'id': c.id, 'titulo': c.titulo, 'mensagem': c.mensagem,
            'data_inicio': c.data_inicio.isoformat() if c.data_inicio else None,
            'data_fim': c.data_fim.isoformat() if c.data_fim else None,
            'ativa': c.ativa,
            'enviada_em': c.enviada_em.isoformat() if c.enviada_em else None,
            'total_enviados': c.total_enviados,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        })

    def delete(self, request, pk):
        try:
            c = self.get_object(pk)
            c.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)


class CampanhaPromocaoEnviarView(APIView):
    """POST /clinica-beleza/campanhas/<id>/enviar/ — envia a mensagem da campanha para todos os pacientes com allow_whatsapp e telefone."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        import logging
        from django.utils import timezone
        logger = logging.getLogger(__name__)
        try:
            campanha = CampanhaPromocao.objects.get(pk=pk)
        except CampanhaPromocao.DoesNotExist:
            return Response({'error': 'Campanha não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not getattr(config, 'whatsapp_ativo', False):
            return Response({'error': 'WhatsApp não está ativo. Configure em Configurações.'}, status=status.HTTP_400_BAD_REQUEST)
        from whatsapp.services import send_whatsapp
        pacientes = Patient.objects.filter(active=True, allow_whatsapp=True).exclude(phone__isnull=True).exclude(phone='')
        enviados = 0
        for p in pacientes:
            if not (getattr(p, 'phone', None) or '').strip():
                continue
            try:
                if send_whatsapp(telefone=p.phone, mensagem=campanha.mensagem, user=request.user, config=config):
                    enviados += 1
            except Exception as e:
                logger.warning("Campanha %s paciente %s: %s", pk, p.id, e)
        campanha.enviada_em = timezone.now()
        campanha.total_enviados = enviados
        campanha.save(update_fields=['enviada_em', 'total_enviados', 'updated_at'])
        return Response({'sent': enviados, 'total_recipients': pacientes.count(), 'message': f'Mensagem enviada para {enviados} paciente(s).'})

