"""
Views de Agenda, Bloqueios de Horário e Agendamentos — Clínica da Beleza
"""
import logging

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_MEMBER
from rest_framework import status

from .models import Appointment, BloqueioHorario
from .serializers import (
    AppointmentCreateSerializer, AgendaEventSerializer,
    BloqueioHorarioSerializer,
)
from .utils import LojaContextHelper
from .views_base import GetObjectMixin
from .agenda_service import (
    AgendaConflictError, AgendaValidationError,
    atualizar_agendamento, detectar_conflito,
)

logger = logging.getLogger(__name__)


def _agenda_events_queryset():
    """Queryset otimizado para AgendaEventSerializer (evita N+1 em appointment_procedures)."""
    return (
        Appointment.objects
        .select_related(
            'patient', 'professional', 'procedure',
            'convenio', 'nome_agenda', 'local_atendimento', 'consulta',
        )
        .prefetch_related('appointment_procedures__procedure')
    )


# ---------------------------------------------------------------------------
# Agenda (calendário FullCalendar)
# ---------------------------------------------------------------------------

class AgendaView(APIView):
    """GET /clinica-beleza/agenda/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        from django.db.models import Q
        qs = (
            _agenda_events_queryset()
            .filter(
                patient__is_active=True,
            )
            .filter(
                Q(professional__isnull=True) | Q(professional__is_active=True)
            )
        )
        if s := request.query_params.get('start'):
            qs = qs.filter(date__gte=s)
        if e := request.query_params.get('end'):
            qs = qs.filter(date__lte=e)
        if p := request.query_params.get('professional'):
            qs = qs.filter(professional_id=p)
        return Response(AgendaEventSerializer(qs.order_by('date'), many=True).data)


class AgendaUpdateView(APIView):
    """PATCH /clinica-beleza/agenda/<id>/update/"""
    permission_classes = CLINICA_MEMBER

    def patch(self, request, pk):
        try:
            appointment = (
                _agenda_events_queryset()
                .get(pk=pk)
            )
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Detecção de conflito offline
        local_version = request.data.get('version')
        resolve_use_local = request.data.get('resolve_use_local') is True
        if not resolve_use_local:
            try:
                detectar_conflito(appointment, local_version, request.data, AgendaEventSerializer)
            except AgendaConflictError as e:
                return Response(
                    {'conflict': True, 'server': e.server_data, 'local': e.local_payload,
                     'resolution_hint': e.resolution_hint},
                    status=status.HTTP_409_CONFLICT,
                )

        new_date = request.data.get('date')
        new_status = request.data.get('status')
        new_duracao = request.data.get('duracao_minutos')

        if not new_date and new_status is None and new_duracao is None and not resolve_use_local:
            return Response(
                {'error': 'Envie date, duracao_minutos e/ou status'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = atualizar_agendamento(
                appointment,
                new_date=new_date,
                new_status=new_status,
                new_duracao=new_duracao,
                user=request.user,
                request=request,
            )
        except AgendaValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

        response_data = AgendaEventSerializer(result.appointment).data
        if result.consulta_id is not None:
            response_data['consulta_id'] = result.consulta_id
        if result.consulta_error:
            response_data['consulta_error'] = result.consulta_error
        return Response(response_data)


class AgendaCreateView(APIView):
    """POST /clinica-beleza/agenda/create/"""
    permission_classes = CLINICA_MEMBER

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from .agenda_service import criar_agendamento
        try:
            appointment = criar_agendamento(
                serializer.validated_data,
                user=request.user,
                request=request,
                serializer=serializer,
            )
            return Response(AgendaEventSerializer(appointment).data, status=status.HTTP_201_CREATED)
        except AgendaValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Erro ao criar agendamento: %s', e)
            return Response(
                {'error': 'Erro ao salvar agendamento. Verifique se a loja está configurada e tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgendaDeleteView(GetObjectMixin, APIView):
    """DELETE /clinica-beleza/agenda/<id>/delete/"""
    permission_classes = CLINICA_MEMBER
    model_class = Appointment
    not_found_message = 'Agendamento não encontrado'

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgendaReenviarMensagemView(APIView):
    """POST /clinica-beleza/agenda/<id>/reenviar-mensagem/"""
    permission_classes = CLINICA_MEMBER

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.select_related('patient').get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({'error': 'Agendamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not getattr(appointment.patient, 'allow_whatsapp', True):
            return Response({'sent': False, 'message': 'Paciente não permite receber WhatsApp.'})
        telefone = (
            getattr(appointment.patient, 'telefone', '')
            or getattr(appointment.patient, 'phone', '')
            or ''
        )
        if not telefone.strip():
            return Response({'sent': False, 'message': 'Paciente sem telefone cadastrado.'})

        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not config.enviar_confirmacao:
            return Response({'sent': False, 'message': 'Envio de confirmação desativado nas Configurações.'})
        if not getattr(config, 'whatsapp_ativo', False):
            return Response({'sent': False, 'message': 'WhatsApp não está ativo. Ative em Configurações → WhatsApp.'})

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
    permission_classes = CLINICA_MEMBER

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
            return Response(
                {'error': 'Erro ao salvar bloqueio. Verifique data/hora e tente novamente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BloqueioHorarioDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/bloqueios/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_MEMBER
    model_class = BloqueioHorario
    not_found_message = 'Bloqueio não encontrado'
    select_related_fields = ['professional']

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(BloqueioHorarioSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = BloqueioHorarioSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
