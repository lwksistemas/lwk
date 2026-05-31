"""
Views de Agenda, Bloqueios de Horário e Agendamentos — Clínica da Beleza
"""
import logging
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Appointment, BloqueioHorario
from .bloqueio_utils import bloqueio_datetime_range, intervalos_sobrepoem
from .serializers import (
    AppointmentListSerializer, AppointmentDetailSerializer,
    AppointmentCreateSerializer, AgendaEventSerializer,
    BloqueioHorarioSerializer,
)
from .utils import LojaContextHelper
from rules.base import MotorRegras

logger = logging.getLogger(__name__)


def _bloqueio_impede_agendamento(data_inicio, data_fim, professional_id, bloqueios_queryset):
    """Retorna True se algum bloqueio sobrepõe o intervalo [data_inicio, data_fim]."""
    if timezone.is_naive(data_inicio):
        data_inicio = timezone.make_aware(data_inicio, timezone.get_current_timezone())
    if timezone.is_naive(data_fim):
        data_fim = timezone.make_aware(data_fim, timezone.get_current_timezone())

    for b in bloqueios_queryset:
        if b.professional_id is not None and b.professional_id != professional_id:
            continue
        b_inicio, b_fim = bloqueio_datetime_range(b)
        if intervalos_sobrepoem(data_inicio, data_fim, b_inicio, b_fim):
            return True
    return False


# ---------------------------------------------------------------------------
# Agendamentos (CRUD simples)
# ---------------------------------------------------------------------------

class AppointmentListView(APIView):
    """GET /clinica-beleza/appointments/  POST /clinica-beleza/appointments/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Appointment.objects.select_related('patient', 'professional', 'procedure')
        if d := request.query_params.get('date'):
            qs = qs.filter(date__date=d)
        if s := request.query_params.get('status'):
            qs = qs.filter(status=s)
        if p := request.query_params.get('professional'):
            qs = qs.filter(professional_id=p)
        return Response(AppointmentListSerializer(qs.order_by('-date'), many=True).data)

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentDetailView(APIView):
    """GET /clinica-beleza/appointments/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Appointment.objects.select_related('patient', 'professional', 'procedure').get(pk=pk)
            return Response(AppointmentDetailSerializer(obj).data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Appointment.objects.get(pk=pk)
            serializer = AppointmentCreateSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            Appointment.objects.get(pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Agenda (calendário FullCalendar)
# ---------------------------------------------------------------------------

class AgendaView(APIView):
    """GET /clinica-beleza/agenda/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Appointment.objects.select_related('patient', 'professional', 'procedure')
        if s := request.query_params.get('start'):
            qs = qs.filter(date__gte=s)
        if e := request.query_params.get('end'):
            qs = qs.filter(date__lte=e)
        if p := request.query_params.get('professional'):
            qs = qs.filter(professional_id=p)
        return Response(AgendaEventSerializer(qs.order_by('date'), many=True).data)


class AgendaHojeView(APIView):
    """GET /clinica-beleza/agenda/hoje/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Appointment.objects
            .select_related('patient', 'professional', 'procedure')
            .filter(date__date=now().date())
            .order_by('date')
        )
        return Response(AgendaEventSerializer(qs, many=True).data)


class AgendaUpdateView(APIView):
    """PATCH /clinica-beleza/agenda/<id>/update/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.select_related('procedure', 'professional', 'patient').get(pk=pk)
            new_date = request.data.get('date')
            new_status = request.data.get('status')
            new_duracao = request.data.get('duracao_minutos')
            local_version = request.data.get('version')
            resolve_use_local = request.data.get('resolve_use_local') is True

            # Detecção de conflito de sincronização
            if local_version is not None and not resolve_use_local:
                if appointment.version != local_version:
                    server_data = AgendaEventSerializer(appointment).data
                    local_payload = {
                        'id': appointment.id, 'version': local_version,
                        'date': request.data.get('date'), 'status': request.data.get('status'),
                        'updated_at': request.data.get('updated_at'),
                    }
                    resolution_hint = None
                    if appointment.status == 'CANCELLED':
                        resolution_hint = 'server_cancelled'
                    elif appointment.updated_at and request.data.get('updated_at'):
                        try:
                            from django.utils.dateparse import parse_datetime
                            local_ts = parse_datetime(request.data.get('updated_at'))
                            if local_ts and local_ts > appointment.updated_at:
                                resolution_hint = 'local_newer'
                        except Exception:
                            pass
                    return Response(
                        {'conflict': True, 'server': server_data, 'local': local_payload, 'resolution_hint': resolution_hint},
                        status=status.HTTP_409_CONFLICT,
                    )

            if new_duracao is not None:
                try:
                    new_duracao = int(new_duracao)
                except (TypeError, ValueError):
                    return Response({'error': 'Duração inválida.'}, status=status.HTTP_400_BAD_REQUEST)
                if new_duracao < 15:
                    return Response({'error': 'Duração mínima de 15 minutos.'}, status=status.HTTP_400_BAD_REQUEST)
                appointment.duracao_minutos = new_duracao

            date_changed = new_date is not None
            if date_changed:
                from django.utils.dateparse import parse_datetime
                date_start = (parse_datetime(new_date) if isinstance(new_date, str) else new_date) or now()
                appointment.date = date_start
            else:
                date_start = appointment.date

            duracao_changed = request.data.get('duracao_minutos') is not None
            if date_changed or duracao_changed:
                date_end = date_start + timedelta(minutes=appointment.get_duracao_efetiva())
                bloqueios = BloqueioHorario.objects.filter(
                    Q(professional_id=appointment.professional_id) | Q(professional_id__isnull=True)
                )
                if _bloqueio_impede_agendamento(date_start, date_end, appointment.professional_id, bloqueios):
                    return Response({'error': 'Horário bloqueado. Escolha outro horário.'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    MotorRegras().executar('AGENDAMENTO_ATUALIZADO', {
                        'profissional': appointment.professional, 'date': date_start,
                        'date_end': date_end, 'appointment_id': appointment.id,
                    })
                except ValidationError as e:
                    return Response({'error': e.messages[0] if e.messages else str(e)}, status=status.HTTP_400_BAD_REQUEST)

            if new_status is not None:
                valid = dict(Appointment.STATUS_CHOICES).keys()
                if new_status not in valid:
                    return Response({'error': f'Status inválido. Use: {", ".join(valid)}'}, status=status.HTTP_400_BAD_REQUEST)
                old_status = appointment.status
                appointment.status = new_status

            if not date_changed and new_status is None and not duracao_changed and not resolve_use_local:
                return Response({'error': 'Envie date, duracao_minutos e/ou status'}, status=status.HTTP_400_BAD_REQUEST)

            appointment.version = (appointment.version or 1) + 1
            appointment.updated_by_id = getattr(request.user, 'id', None)
            appointment.save()

            consulta_id = None
            consulta_error = None
            if new_status is not None:
                from .consulta_service import sync_consulta_from_appointment_status
                try:
                    consulta = sync_consulta_from_appointment_status(appointment, new_status, old_status)
                    if consulta:
                        consulta_id = consulta.id
                except Exception as e:
                    logger.exception('Erro ao sincronizar consulta agendamento %s status %s: %s', pk, new_status, e)
                    consulta_error = 'Consulta não criada. Execute a atualização do sistema ou contate o suporte.'

            if new_status == 'COMPLETED':
                try:
                    MotorRegras().executar('AGENDAMENTO_FINALIZADO', {'appointment': appointment})
                except Exception:
                    pass

            if new_status == 'CONFIRMED':
                try:
                    if getattr(appointment.patient, 'allow_whatsapp', True):
                        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
                        if config and config.enviar_confirmacao:
                            from whatsapp.services import enviar_confirmacao_agendamento
                            enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
                except Exception as e:
                    logger.warning('WhatsApp confirmação agendamento %s: %s', pk, e)

            response_data = AgendaEventSerializer(appointment).data
            if consulta_id is not None:
                response_data['consulta_id'] = consulta_id
            if consulta_error:
                response_data['consulta_error'] = consulta_error
            return Response(response_data)

        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class AgendaCreateView(APIView):
    """POST /clinica-beleza/agenda/create/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            date_start = data['date']
            date_end = date_start + timedelta(minutes=data['procedure'].duracao_minutos)
            professional_id = data['professional'].id
            bloqueios = BloqueioHorario.objects.filter(
                Q(professional_id=professional_id) | Q(professional_id__isnull=True)
            )
            if _bloqueio_impede_agendamento(date_start, date_end, professional_id, bloqueios):
                return Response({'error': 'Horário bloqueado. Escolha outro horário ou profissional.'}, status=status.HTTP_400_BAD_REQUEST)

            motor = MotorRegras()
            try:
                motor.executar('AGENDAMENTO_CRIADO', {
                    'profissional': data['professional'], 'date': date_start,
                    'date_end': date_end, 'appointment_id': None,
                })
            except ValidationError as e:
                return Response({'error': e.messages[0] if e.messages else str(e)}, status=status.HTTP_400_BAD_REQUEST)

            appointment = serializer.save()

            try:
                motor.executar('AGENDAMENTO_CRIADO', {
                    'profissional': appointment.professional, 'date': appointment.date,
                    'date_end': appointment.date + timedelta(minutes=appointment.get_duracao_efetiva()),
                    'appointment_id': appointment.id, 'appointment': appointment,
                })
            except Exception:
                pass

            # WhatsApp: confirmação ao criar
            if appointment.status in ('CONFIRMED', 'SCHEDULED') and getattr(appointment.patient, 'allow_whatsapp', True):
                try:
                    if (getattr(appointment.patient, 'phone', None) or '').strip():
                        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
                        if config and config.enviar_confirmacao:
                            from whatsapp.services import enviar_confirmacao_agendamento
                            enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
                except Exception as e:
                    logger.warning('WhatsApp confirmação ao criar agendamento %s: %s', appointment.id, e)

            return Response(AgendaEventSerializer(appointment).data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': e.messages[0] if e.messages else str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Erro ao criar agendamento: %s', e)
            return Response({'error': 'Erro ao salvar agendamento. Verifique se a loja está configurada e tente novamente.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgendaDeleteView(APIView):
    """DELETE /clinica-beleza/agenda/<id>/delete/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            Appointment.objects.get(pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class AgendaReenviarMensagemView(APIView):
    """POST /clinica-beleza/agenda/<id>/reenviar-mensagem/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not getattr(appointment.patient, 'allow_whatsapp', True):
            return Response({'sent': False, 'message': 'Paciente não permite receber WhatsApp.'})
        if not (getattr(appointment.patient, 'phone', None) or '').strip():
            return Response({'sent': False, 'message': 'Paciente sem telefone cadastrado.'})

        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not config.enviar_confirmacao:
            return Response({'sent': False, 'message': 'Envio de confirmação desativado nas Configurações.'})

        from whatsapp.services import enviar_confirmacao_agendamento
        try:
            ok, err_msg = enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
            if ok:
                return Response({'sent': True, 'message': 'Mensagem reenviada com sucesso.'})
            return Response({'sent': False, 'message': err_msg or 'Não foi possível enviar.'})
        except Exception as e:
            logger.warning('WhatsApp reenvio agendamento %s: %s', pk, e)
            return Response({'sent': False, 'message': f'Erro ao enviar: {str(e)}'})


# ---------------------------------------------------------------------------
# Bloqueios de Horário
# ---------------------------------------------------------------------------

class BloqueioHorarioListView(APIView):
    """GET /clinica-beleza/bloqueios/  POST /clinica-beleza/bloqueios/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = BloqueioHorario.objects.all().select_related('professional').order_by('-data_inicio')
        if s := request.query_params.get('start'):
            qs = qs.filter(data_fim__gte=s)
        if e := request.query_params.get('end'):
            qs = qs.filter(data_inicio__lte=e)
        if p := request.query_params.get('professional'):
            qs = qs.filter(Q(professional_id=p) | Q(professional_id__isnull=True))
        return Response(BloqueioHorarioSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BloqueioHorarioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception('Erro ao criar BloqueioHorario: %s', e)
            return Response({'error': 'Erro ao salvar bloqueio. Verifique data/hora e tente novamente.'}, status=status.HTTP_400_BAD_REQUEST)


class BloqueioHorarioDetailView(APIView):
    """GET /clinica-beleza/bloqueios/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(BloqueioHorarioSerializer(BloqueioHorario.objects.select_related('professional').get(pk=pk)).data)
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
            BloqueioHorario.objects.get(pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BloqueioHorario.DoesNotExist:
            return Response({'error': 'Bloqueio não encontrado'}, status=status.HTTP_404_NOT_FOUND)
