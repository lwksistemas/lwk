"""Criar, alterar, excluir e reenviar confirmação de agendamento."""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.agenda_service import (
    AgendaConflictError,
    AgendaValidationError,
    atualizar_agendamento,
    detectar_conflito,
    horario_agendamento_passou,
)
from clinica_beleza.models import Appointment
from clinica_beleza.permissions import (
    CLINICA_AGENDA,
    appointment_in_agenda_scope,
    resolve_agenda_professional_scope,
)
from clinica_beleza.serializers import AgendaEventSerializer, AppointmentCreateSerializer
from clinica_beleza.utils import LojaContextHelper
from clinica_beleza.views_agenda.helpers import (
    _agenda_events_queryset,
    _agenda_scope_forbidden_response,
)
from clinica_beleza.views_base import GetObjectMixin

logger = logging.getLogger(__name__)


class AgendaUpdateView(GetObjectMixin, APIView):
    """PATCH /clinica-beleza/agenda/<id>/update/"""

    permission_classes = CLINICA_AGENDA
    model_class = Appointment
    not_found_message = "Agendamento não encontrado"

    def get_object(self, pk):
        try:
            return _agenda_events_queryset().get(pk=pk)
        except Appointment.DoesNotExist:
            return None

    def patch(self, request, pk):
        logger.info("PATCH agenda/%s data=%s", pk, dict(request.data))
        appointment, err = self.object_or_404(pk)
        if err:
            return err

        scope = resolve_agenda_professional_scope(request)
        if not appointment_in_agenda_scope(appointment, scope):
            return _agenda_scope_forbidden_response()

        local_version = request.data.get("version")
        resolve_use_local = request.data.get("resolve_use_local") is True
        if not resolve_use_local:
            try:
                detectar_conflito(appointment, local_version, request.data, AgendaEventSerializer)
            except AgendaConflictError as e:
                return Response(
                    {"conflict": True, "server": e.server_data, "local": e.local_payload,
                     "resolution_hint": e.resolution_hint},
                    status=status.HTTP_409_CONFLICT,
                )

        new_date = request.data.get("date")
        new_status = request.data.get("status")
        new_duracao = request.data.get("duracao_minutos")
        new_professional = request.data.get("professional")
        new_procedures_ids = request.data.get("procedures_ids")

        if (
            not new_date
            and new_status is None
            and new_duracao is None
            and new_professional is None
            and new_procedures_ids is None
            and not resolve_use_local
        ):
            return Response(
                {"error": "Envie date, duracao_minutos, professional, procedures_ids e/ou status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if scope is not None and new_professional is not None and str(new_professional) != str(scope):
            return _agenda_scope_forbidden_response()

        try:
            result = atualizar_agendamento(
                appointment,
                new_date=new_date,
                new_status=new_status,
                new_duracao=new_duracao,
                new_professional=new_professional,
                new_procedures_ids=new_procedures_ids,
                user=request.user,
                request=request,
            )
        except AgendaValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)

        response_data = AgendaEventSerializer(result.appointment).data
        logger.info(
            "PATCH agenda/%s saved start=%s version=%s",
            pk,
            response_data.get("start"),
            response_data.get("version"),
        )
        if result.consulta_id is not None:
            response_data["consulta_id"] = result.consulta_id
        if result.consulta_error:
            response_data["consulta_error"] = result.consulta_error
        if result.confirmacao_reiniciada:
            response_data["confirmacao_reiniciada"] = True
        return Response(response_data)


class AgendaCreateView(APIView):
    """POST /clinica-beleza/agenda/create/"""

    permission_classes = CLINICA_AGENDA

    def post(self, request):
        scope = resolve_agenda_professional_scope(request)
        data = dict(request.data)
        if scope is not None:
            if scope and str(data.get("professional") or scope) != str(scope):
                return _agenda_scope_forbidden_response()
            data["professional"] = scope
        serializer = AppointmentCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from clinica_beleza.agenda_service import criar_agendamento
        from clinica_beleza.protocolo_comercial import ProtocoloAgendaConflito, agendar_protocolo_da_selecao

        procedures = list(serializer.validated_data.get("_procedures_list") or [])
        if not procedures and serializer.validated_data.get("procedure"):
            procedures = [serializer.validated_data["procedure"]]
        forma = str(request.data.get("forma_cobranca") or "").strip()
        try:
            resultado = agendar_protocolo_da_selecao(
                procedures=procedures,
                patient=serializer.validated_data.get("patient"),
                professional=serializer.validated_data.get("professional"),
                local_atendimento=serializer.validated_data.get("local_atendimento"),
                data_inicio=serializer.validated_data.get("date"),
                forma_cobranca=forma,
                request=request,
                convenio=serializer.validated_data.get("convenio"),
                nome_agenda=serializer.validated_data.get("nome_agenda"),
                observacao=serializer.validated_data.get("notes") or "",
            )
        except ProtocoloAgendaConflito as exc:
            return Response(
                {"error": str(exc), "conflitos": exc.conflitos},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AgendaValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
        if resultado is not None:
            appointment = Appointment.objects.select_related(
                "patient",
                "professional",
                "procedure",
                "convenio",
                "nome_agenda",
                "local_atendimento",
            ).get(pk=resultado["agendamentos"][0]["id"])
            data = AgendaEventSerializer(appointment).data
            data["sessoes_criadas"] = len(resultado["agendamentos"])
            return Response(data, status=status.HTTP_201_CREATED)

        try:
            appointment = criar_agendamento(
                serializer.validated_data,
                user=request.user,
                request=request,
                serializer=serializer,
            )
            return Response(AgendaEventSerializer(appointment).data, status=status.HTTP_201_CREATED)
        except AgendaValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Erro ao criar agendamento: %s", e)
            return Response(
                {"error": "Erro ao salvar agendamento. Verifique se a loja está configurada e tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgendaDeleteView(GetObjectMixin, APIView):
    """DELETE /clinica-beleza/agenda/<id>/delete/"""

    permission_classes = CLINICA_AGENDA
    model_class = Appointment
    not_found_message = "Agendamento não encontrado"
    select_related_fields = ("consulta",)

    def delete(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        scope = resolve_agenda_professional_scope(request)
        if not appointment_in_agenda_scope(obj, scope):
            return _agenda_scope_forbidden_response()

        if horario_agendamento_passou(obj):
            return Response(
                {"error": "Não é possível excluir um agendamento cujo horário passou há mais de 2 dias."},
                status=status.HTTP_403_FORBIDDEN,
            )

        consulta = getattr(obj, "consulta", None)
        if consulta and consulta.status in ("COMPLETED", "IN_PROGRESS"):
            msg = (
                "Não é possível excluir um agendamento com consulta finalizada ou em andamento. "
                "Cancele a consulta primeiro se necessário."
            )
            return Response({"error": msg}, status=status.HTTP_403_FORBIDDEN)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgendaReenviarMensagemView(APIView):
    """POST /clinica-beleza/agenda/<id>/reenviar-mensagem/"""

    permission_classes = CLINICA_AGENDA

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.select_related("patient").get(pk=pk)
        except Appointment.DoesNotExist:
            return Response({"error": "Agendamento não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        scope = resolve_agenda_professional_scope(request)
        if not appointment_in_agenda_scope(appointment, scope):
            return _agenda_scope_forbidden_response()

        if horario_agendamento_passou(appointment):
            return Response({
                "sent": False,
                "message": "O horário passou há mais de 2 dias. A confirmação não é reenviada.",
            })

        if not getattr(appointment.patient, "allow_whatsapp", True):
            return Response({"sent": False, "message": "Paciente não permite receber WhatsApp."})
        telefone = (
            getattr(appointment.patient, "telefone", "")
            or getattr(appointment.patient, "phone", "")
            or ""
        )
        if not telefone.strip():
            return Response({"sent": False, "message": "Paciente sem telefone cadastrado."})

        config, _ = LojaContextHelper.get_whatsapp_config(request=request)
        if not config or not config.enviar_confirmacao:
            return Response({"sent": False, "message": "Envio de confirmação desativado nas Configurações."})
        if not getattr(config, "whatsapp_ativo", False):
            return Response({"sent": False, "message": "WhatsApp não está ativo. Ative em Configurações → WhatsApp."})

        from clinica_beleza.agenda_confirmacao_service import STATUS_ACIONAVEIS

        if appointment.status not in STATUS_ACIONAVEIS:
            return Response({
                "sent": False,
                "message": (
                    'Só é possível enviar confirmação quando o status é '
                    '"Aguardando confirmação". '
                    f'Status atual: {appointment.get_status_display()}.'
                ),
            })

        from whatsapp.services import enviar_confirmacao_agendamento
        try:
            ok, err_msg = enviar_confirmacao_agendamento(appointment, user=request.user, config=config)
            if ok:
                return Response({"sent": True, "message": "Mensagem reenviada com sucesso."})
            return Response({"sent": False, "message": err_msg or "Não foi possível enviar."})
        except Exception:
            logger.exception("WhatsApp reenvio agendamento %s", pk)
            return Response({"sent": False, "message": "Não foi possível enviar. Tente novamente."})
