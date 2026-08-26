"""Service layer para Agenda — Clínica da Beleza.

Extrai a lógica de negócio que antes ficava diretamente nas views de agenda
(validação de bloqueios, detecção de conflitos, regras, side-effects).
"""
import logging
import threading
from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from .bloqueio_utils import bloqueio_datetime_range, intervalos_sobrepoem
from .models import Appointment, BloqueioHorario, Consulta, Professional

logger = logging.getLogger(__name__)


class AgendaConflictError(Exception):
    """Erro de conflito de sincronização offline (version mismatch)."""

    def __init__(self, server_data, local_payload, resolution_hint=None):
        self.server_data = server_data
        self.local_payload = local_payload
        self.resolution_hint = resolution_hint
        super().__init__("Conflito de sincronização")


class AgendaValidationError(Exception):
    """Erro de validação de regras de negócio da agenda."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Validações compartilhadas
# ---------------------------------------------------------------------------

def bloqueio_impede_agendamento(data_inicio, data_fim, professional_id):
    """Verifica se algum bloqueio ativo impede o agendamento no intervalo.
    Retorna True se houver sobreposição.
    """
    from django.utils import timezone

    if timezone.is_naive(data_inicio):
        data_inicio = timezone.make_aware(data_inicio, timezone.get_current_timezone())
    if timezone.is_naive(data_fim):
        data_fim = timezone.make_aware(data_fim, timezone.get_current_timezone())

    data_inicio_date = data_inicio.date()
    data_fim_date = data_fim.date()

    bloqueios = BloqueioHorario.objects.filter(
        Q(professional_id=professional_id) | Q(professional_id__isnull=True),
        data_inicio__lte=data_fim_date,
        data_fim__gte=data_inicio_date,
    )
    for b in bloqueios:
        if b.professional_id is not None and b.professional_id != professional_id:
            continue
        b_inicio, b_fim = bloqueio_datetime_range(b)
        if intervalos_sobrepoem(data_inicio, data_fim, b_inicio, b_fim):
            return True
    return False


def validar_regras_agendamento(evento: str, professional, date_start, date_end, appointment_id=None):
    """Executa o motor de regras para o evento (AGENDAMENTO_CRIADO ou AGENDAMENTO_ATUALIZADO).
    Lança AgendaValidationError se alguma regra falhar.
    """
    from rules.base import MotorRegras
    try:
        MotorRegras().executar(evento, {
            "profissional": professional,
            "date": date_start,
            "date_end": date_end,
            "appointment_id": appointment_id,
        })
    except ValidationError as e:
        raise AgendaValidationError(e.messages[0] if e.messages else str(e))


# ---------------------------------------------------------------------------
# Detecção de conflito offline
# ---------------------------------------------------------------------------

def versao_int(value):
    """Normaliza version do client (JSON number ou string) para int."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def detectar_conflito(appointment, local_version, request_data, serializer_class):
    """Detecta conflito de versão entre o servidor e o client.
    Lança AgendaConflictError se houver conflito.
    """
    local_version = versao_int(local_version)
    if local_version is None:
        return
    if versao_int(appointment.version) == local_version:
        return

    server_data = serializer_class(appointment).data
    local_payload = {
        "id": appointment.id,
        "version": local_version,
        "date": request_data.get("date"),
        "status": request_data.get("status"),
        "updated_at": request_data.get("updated_at"),
    }
    resolution_hint = None
    if appointment.status == "CANCELLED":
        resolution_hint = "server_cancelled"
    elif appointment.updated_at and request_data.get("updated_at"):
        try:
            local_ts = parse_datetime(request_data.get("updated_at"))
            if local_ts and local_ts > appointment.updated_at:
                resolution_hint = "local_newer"
        except Exception:
            pass
    raise AgendaConflictError(server_data, local_payload, resolution_hint)


# ---------------------------------------------------------------------------
# Criar agendamento
# ---------------------------------------------------------------------------

def criar_agendamento(validated_data, *, user=None, request=None, serializer=None):
    """Cria um agendamento com todas as validações de negócio.
    Retorna o Appointment criado.
    Lança AgendaValidationError se bloqueio ou regra impedir.

    Se `serializer` for passado, usa serializer.save() (suporta múltiplos procedimentos).
    """
    date_start = validated_data["date"]
    professional = validated_data.get("professional")
    local_atendimento = validated_data.get("local_atendimento")

    from .duracao_consulta import calcular_duracao_novo_agendamento
    procedures_list = validated_data.get("_procedures_list")
    total_duration = calcular_duracao_novo_agendamento(
        professional=professional,
        procedures_list=procedures_list,
        procedure=validated_data.get("procedure"),
        local_atendimento=local_atendimento,
    )

    date_end = date_start + timedelta(minutes=total_duration)

    # Verificar bloqueios (apenas se tem profissional definido)
    if professional and bloqueio_impede_agendamento(date_start, date_end, professional.id):
        raise AgendaValidationError("Horário bloqueado. Escolha outro horário ou profissional.")

    # Regras de negócio (pré-criação) — apenas se tem profissional
    if professional:
        validar_regras_agendamento(
            "AGENDAMENTO_CRIADO", professional, date_start, date_end, appointment_id=None,
        )

    # Criar via serializer (lida com AppointmentProcedure) ou direto
    if serializer:
        appointment = serializer.save()
    else:
        clean_data = {k: v for k, v in validated_data.items() if not k.startswith("_")}
        appointment = Appointment.objects.create(**clean_data)

    # Regras pós-criação (best-effort)
    try:
        from rules.base import MotorRegras
        MotorRegras().executar("AGENDAMENTO_CRIADO", {
            "profissional": appointment.professional,
            "date": appointment.date,
            "date_end": appointment.date + timedelta(minutes=appointment.get_duracao_efetiva()),
            "appointment_id": appointment.id,
            "appointment": appointment,
        })
    except Exception:
        logger.exception("Erro ao executar regras pós-criação do agendamento %s", appointment.id)

    # Link de confirmação: só na criação se hoje já é um dia de envio
    # (regra exata, ou última chance — ex.: consulta hoje com "1 dia antes").
    try:
        from whatsapp.confirmacao_agenda_service import disparar_confirmacao_se_hoje

        disparar_confirmacao_se_hoje(appointment)
    except Exception:
        logger.exception(
            "WhatsApp confirmação na criação do agendamento %s", appointment.id,
        )

    return appointment


# ---------------------------------------------------------------------------
# Atualizar agendamento
# ---------------------------------------------------------------------------

@dataclass
class UpdateResult:
    appointment: Appointment
    consulta_id: int | None = None
    consulta_error: str | None = None


def _profissional_ativo(new_professional):
    try:
        pid = int(new_professional)
    except (TypeError, ValueError):
        raise AgendaValidationError("Profissional inválido.")
    prof = Professional.objects.filter(pk=pid, is_active=True).first()
    if not prof:
        raise AgendaValidationError("Profissional não encontrado.")
    return prof


def _sync_consulta_profissional(appointment, prof):
    try:
        consulta = appointment.consulta
    except Consulta.DoesNotExist:
        return
    if consulta.professional_id == prof.id:
        return
    consulta.professional = prof
    consulta.save(update_fields=["professional", "updated_at"])


def atualizar_agendamento(appointment, *, new_date=None, new_status=None,
                          new_duracao=None, new_professional=None, user=None, request=None) -> UpdateResult:
    """Atualiza um agendamento com validações de negócio.
    Retorna UpdateResult com dados do resultado.
    Lança AgendaValidationError se alguma validação falhar.
    """
    date_changed = new_date is not None
    duracao_changed = new_duracao is not None
    professional_changed = False
    old_status = appointment.status

    # Duração
    if new_duracao is not None:
        try:
            new_duracao = int(new_duracao)
        except (TypeError, ValueError):
            raise AgendaValidationError("Duração inválida.")
        if new_duracao < 5:
            raise AgendaValidationError("Duração mínima de 5 minutos.")
        appointment.duracao_minutos = new_duracao

    # Profissional
    if new_professional is not None and new_professional != "":
        prof = _profissional_ativo(new_professional)
        if appointment.professional_id != prof.id:
            appointment.professional = prof
            professional_changed = True
            _sync_consulta_profissional(appointment, prof)

    # Data
    if date_changed:
        date_start = (parse_datetime(new_date) if isinstance(new_date, str) else new_date) or now()
        appointment.date = date_start
    else:
        date_start = appointment.date

    # Validar bloqueios e regras se data, duração ou profissional mudou
    if date_changed or duracao_changed or professional_changed:
        date_end = date_start + timedelta(minutes=appointment.get_duracao_efetiva())
        if bloqueio_impede_agendamento(date_start, date_end, appointment.professional_id):
            raise AgendaValidationError("Horário bloqueado. Escolha outro horário.")
        validar_regras_agendamento(
            "AGENDAMENTO_ATUALIZADO", appointment.professional,
            date_start, date_end, appointment_id=appointment.id,
        )

    # Status
    if new_status is not None:
        valid = dict(Appointment.STATUS_CHOICES).keys()
        if new_status not in valid:
            raise AgendaValidationError(f'Status inválido. Use: {", ".join(valid)}')
        if new_status in ("IN_PROGRESS", "COMPLETED"):
            raise AgendaValidationError(
                "Em atendimento e concluído são alterados em Consultas "
                "(iniciar / finalizar consulta).",
            )
        appointment.status = new_status

    # Salvar
    appointment.version = (appointment.version or 1) + 1
    appointment.updated_by_id = getattr(user, "id", None) if user else None
    appointment.save()

    # Side effects
    result = UpdateResult(appointment=appointment)

    if new_status is not None:
        result.consulta_id, result.consulta_error = _sync_consulta(appointment, new_status, old_status)

    # Data/profissional gravados; WhatsApp de remarcação vai em segundo plano (não segura o PATCH).
    if date_changed or professional_changed:
        _redisparar_confirmacao_por_mudanca_data(appointment)

    return result


# ---------------------------------------------------------------------------
# Side effects (internos)
# ---------------------------------------------------------------------------

def _sync_consulta(appointment, new_status, old_status):
    """Sincroniza consulta com o novo status. Retorna (consulta_id, error_msg)."""
    from .consulta_service import sync_consulta_from_appointment_status
    try:
        consulta = sync_consulta_from_appointment_status(appointment, new_status, old_status)
        return (consulta.id if consulta else None), None
    except Exception as e:
        logger.exception("Erro ao sincronizar consulta agendamento %s status %s: %s",
                         appointment.id, new_status, e)
        return None, "Consulta não criada. Execute a atualização do sistema ou contate o suporte."


def enviar_confirmacao_reagendamento(appointment_id: int, loja_id: int) -> None:
    """Worker/thread: envia WhatsApp após remarcar, fora do PATCH da agenda."""
    from django.db import connections
    from superadmin.models import Loja
    from tenants.middleware import _configure_tenant_db_for_loja
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import enviar_confirmacao_agendamento

    try:
        loja = Loja.objects.using("default").filter(pk=loja_id).first()
        if not loja:
            logger.warning("Reagendamento WhatsApp: loja %s não encontrada", loja_id)
            return
        _configure_tenant_db_for_loja(loja)
        appointment = (
            Appointment.objects.select_related("patient", "professional", "procedure")
            .filter(pk=appointment_id)
            .first()
        )
        if not appointment:
            return
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return
        if not getattr(config, "enviar_confirmacao", False):
            return
        ok, err = enviar_confirmacao_agendamento(appointment, config=config, reagendado=True)
        if not ok:
            logger.warning(
                "Re-envio confirmação após mudança de data agendamento %s falhou: %s",
                appointment_id, err,
            )
    except Exception:
        logger.exception(
            "Erro ao enviar confirmação de reagendamento do agendamento %s",
            appointment_id,
        )
    finally:
        connections.close_all()


def _agendar_confirmacao_reagendamento(appointment_id: int, loja_id: int) -> None:
    """Enfileira ou dispara em thread — nunca bloqueia o PATCH da agenda."""
    from core.task_queue import task_queue_enabled

    task_name = f"agenda-reagend-{appointment_id}"
    func_path = "clinica_beleza.agenda_service.enviar_confirmacao_reagendamento"
    if task_queue_enabled():
        try:
            from django_q.tasks import async_task

            async_task(func_path, appointment_id, loja_id, task_name=task_name)
            return
        except Exception as exc:
            logger.warning("Fila indisponível para reagendamento WhatsApp: %s", exc)
    threading.Thread(
        target=enviar_confirmacao_reagendamento,
        args=(appointment_id, loja_id),
        daemon=True,
        name=task_name,
    ).start()


def _redisparar_confirmacao_por_mudanca_data(appointment):
    """Limpa registros de envio anteriores e agenda nova confirmação WhatsApp.

    Quando o agendamento é arrastado para outro horário, a mensagem antiga fica
    com a data errada. O envio roda em segundo plano para o PATCH responder
    na hora — senão o arrasto na agenda falha de forma intermitente.
    """
    try:
        from whatsapp.models import WhatsAppConfirmacaoEnvio, WhatsAppConfig
        from tenants.middleware import get_current_loja_id

        WhatsAppConfirmacaoEnvio.objects.filter(
            appointment_id=appointment.id,
        ).delete()

        loja_id = getattr(appointment, "loja_id", None) or get_current_loja_id()
        if not loja_id:
            return
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return
        if not getattr(config, "enviar_confirmacao", False):
            return

        _agendar_confirmacao_reagendamento(appointment.id, loja_id)
    except Exception:
        logger.exception(
            "Erro ao re-disparar confirmação após mudança de data do agendamento %s",
            appointment.id,
        )


def _executar_regra_finalizacao(appointment):
    """Executa regras de finalização (best-effort)."""
    try:
        from rules.base import MotorRegras
        MotorRegras().executar("AGENDAMENTO_FINALIZADO", {"appointment": appointment})
    except Exception:
        logger.exception("Erro ao executar regras de finalização do agendamento %s", appointment.id)


