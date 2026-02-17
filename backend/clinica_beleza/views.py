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
from datetime import timedelta, date
from .models import Patient, Professional, Procedure, Appointment, Payment, BloqueioHorario
from rules.base import MotorRegras
from .serializers import (
    PatientSerializer, ProfessionalSerializer, ProfessionalCreateWithUserSerializer,
    ProcedureSerializer,
    AppointmentListSerializer, AppointmentDetailSerializer, AppointmentCreateSerializer,
    PaymentSerializer, AgendaEventSerializer, BloqueioHorarioSerializer
)
from tenants.middleware import get_current_loja_id


def _get_owner_professional_id():
    """ID do Professional (schema tenant) vinculado ao owner da loja atual. None se não houver."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from superadmin.models import Loja, ProfissionalUsuario
        loja = Loja.objects.using('default').get(id=loja_id)
        pu = ProfissionalUsuario.objects.using('default').filter(
            loja_id=loja_id, user_id=loja.owner_id
        ).first()
        return pu.professional_id if pu else None
    except Exception:
        return None


def _get_loja_owner_info():
    """Dados do administrador da loja atual: username, email, telefone. None se não houver contexto."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').select_related('owner').get(id=loja_id)
        return {
            'owner_username': loja.owner.username,
            'owner_email': loja.owner.email or '',
            'owner_telefone': getattr(loja, 'owner_telefone', '') or '',
        }
    except Exception:
        return None


class LojaInfoView(APIView):
    """
    Informações da loja atual (administrador) para exibir na interface.
    GET /clinica-beleza/loja-info/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = _get_loja_owner_info()
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
        owner_professional_id = _get_owner_professional_id()
        serializer = ProfessionalSerializer(
            queryset, many=True,
            context={'owner_professional_id': owner_professional_id}
        )
        return Response(serializer.data)

    def post(self, request):
        import logging
        log = logging.getLogger(__name__)
        data = dict(request.data)
        # Normalizar email/phone vazios para None (evita 400 em ProfessionalSerializer)
        if data.get('email') == '':
            data['email'] = None
        if data.get('phone') == '':
            data['phone'] = None
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
        serializer = ProfessionalSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        log.warning('POST professionals: validation errors %s', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE. O administrador vinculado à loja não pode ser editado nem excluído."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            owner_professional_id = _get_owner_professional_id()
            return Response(ProfessionalSerializer(
                obj, context={'owner_professional_id': owner_professional_id}
            ).data)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        owner_professional_id = _get_owner_professional_id()
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
        owner_professional_id = _get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response(
                {'error': 'O administrador vinculado à loja não pode ser excluído.'},
                status=status.HTTP_403_FORBIDDEN
            )
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
                    from whatsapp.models import WhatsAppConfig
                    from superadmin.models import Loja
                    loja_id = get_current_loja_id()
                    if loja_id and getattr(appointment.patient, 'allow_whatsapp', True):
                        loja = Loja.objects.using('default').filter(id=loja_id).first()
                        if loja:
                            config = getattr(loja, 'whatsapp_config', None) or WhatsAppConfig.objects.filter(loja=loja).first()
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
                    from whatsapp.models import WhatsAppConfig
                    from superadmin.models import Loja
                    loja_id = get_current_loja_id()
                    patient_phone = getattr(appointment.patient, 'phone', None) or ''
                    if not (patient_phone and str(patient_phone).strip()):
                        logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — paciente sem telefone", appointment.id)
                    elif not loja_id:
                        logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — contexto de loja ausente", appointment.id)
                    else:
                        loja = Loja.objects.using('default').filter(id=loja_id).first()
                        if not loja:
                            logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — loja não encontrada", appointment.id)
                        else:
                            config = getattr(loja, 'whatsapp_config', None) or WhatsAppConfig.objects.filter(loja=loja).first()
                            if not config:
                                logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — config da loja não encontrada", appointment.id)
                            elif not config.enviar_confirmacao:
                                logger.info("WhatsApp: confirmação não enviada ao criar agendamento id=%s — opção 'enviar confirmação' desligada nas Configurações", appointment.id)
                            else:
                                from whatsapp.services import enviar_confirmacao_agendamento
                                if enviar_confirmacao_agendamento(appointment, user=request.user, config=config):
                                    logger.info("WhatsApp confirmação enviada ao criar agendamento id=%s", appointment.id)
                                else:
                                    logger.info(
                                        "WhatsApp: confirmação não enviada ao criar agendamento id=%s — "
                                        "API do WhatsApp Business (Meta) não configurada. Configure Phone ID e Token nas variáveis do servidor ou na integração.",
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

