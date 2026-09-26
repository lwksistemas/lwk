"""Auto-finalização de consultas esquecidas.

Regras (margem: 5h após o fim do horário agendado = início + duração):
1. Consulta IN_PROGRESS (profissional iniciou e esqueceu de finalizar).
2. Agenda em Cliente presente (CONFIRMED) sem a profissional iniciar a consulta.

No caso 2, finaliza no horário marcado (início/fim do slot), sem mover a agenda.
Roda a cada 15 min no worker Django-Q e no cron LWK.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

MARGEM_APOS_FIM_AGENDAMENTO_HORAS = 5
_STATUS_CONSULTA_SEM_INICIAR = frozenset({"SCHEDULED", "RECEBER"})


def _lojas_clinica_beleza():
    from .catalogo_service import lojas_clinica_beleza_com_schema

    return lojas_clinica_beleza_com_schema(apenas_ativas=True)


def _duracao_minutos(appointment) -> int:
    duracao = 30
    if appointment is not None and hasattr(appointment, "get_duracao_efetiva"):
        try:
            duracao = int(appointment.get_duracao_efetiva() or 30)
        except Exception:
            duracao = 30
    if duracao < 1:
        duracao = 30
    return duracao


def _inicio_agendamento(appointment=None, consulta=None):
    if appointment is not None:
        inicio = getattr(appointment, "date", None)
        if inicio is not None:
            return inicio
    if consulta is not None:
        return getattr(consulta, "data_inicio", None)
    return None


def _fim_agendamento(consulta=None, appointment=None):
    """Fim previsto do horário agendado: data do appointment + duração efetiva."""
    appointment = appointment or (getattr(consulta, "appointment", None) if consulta else None)
    inicio = _inicio_agendamento(appointment=appointment, consulta=consulta)
    if inicio is None:
        return None
    return inicio + timedelta(minutes=_duracao_minutos(appointment))


def _horario_limite_finalizacao(consulta=None, appointment=None) -> timezone.datetime | None:
    """Horário em que pode auto-finalizar (fim do agendamento + 5h)."""
    fim = _fim_agendamento(consulta=consulta, appointment=appointment)
    if fim is None:
        return None
    return fim + timedelta(hours=MARGEM_APOS_FIM_AGENDAMENTO_HORAS)


def _finalizar_com_horario_agendado(consulta) -> None:
    """Finaliza usando início/fim do slot agendado (não o momento do job)."""
    from .consulta_service import finalizar_consulta

    appointment = consulta.appointment
    inicio = _inicio_agendamento(appointment=appointment, consulta=consulta)
    fim = _fim_agendamento(consulta=consulta, appointment=appointment)
    if inicio is None or fim is None:
        raise ValueError("Agendamento sem data/duração para auto-finalizar.")

    finalizar_consulta(
        consulta,
        skip_estoque=True,
        permitir_sem_iniciar=True,
        data_inicio_forcada=inicio,
        data_fim_forcada=fim,
    )


def _garantir_consulta_cliente_presente(appointment):
    """Garante Consulta vinculada ao Cliente presente (CONFIRMED)."""
    from clinica_beleza import consulta_service

    consulta = getattr(appointment, "consulta", None)
    if consulta is not None:
        return consulta
    return consulta_service.sync_consulta_from_appointment_status(
        appointment, "CONFIRMED", None,
    )


def _finalizar_em_andamento_esquecidas(agora) -> int:
    from .consulta_service import finalizar_consulta
    from .models import Consulta

    total = 0
    qs = (
        Consulta.objects
        .filter(status="IN_PROGRESS", data_inicio__isnull=False)
        .select_related("appointment", "appointment__professional", "patient")
        .prefetch_related("appointment__appointment_procedures__procedure")
    )
    for consulta in qs.iterator(chunk_size=100):
        try:
            limite = _horario_limite_finalizacao(consulta=consulta)
            if limite is None or agora < limite:
                continue
            finalizar_consulta(consulta, skip_estoque=True)
            total += 1
            logger.info(
                "Auto-finalização (em andamento): consulta=%s paciente=%s limite=%s",
                consulta.id,
                consulta.patient.nome if consulta.patient_id else "?",
                limite.isoformat(),
            )
        except Exception as exc:
            logger.warning(
                "Auto-finalização (em andamento) falhou: consulta=%s: %s",
                consulta.id, exc,
            )
    return total


def _finalizar_cliente_presente_sem_iniciar(agora) -> int:
    """Cliente presente na agenda sem a profissional iniciar → finaliza no horário marcado."""
    from .models import Appointment

    total = 0
    # Janela larga: início do slot no passado; o limite +5h é checado por item.
    qs = (
        Appointment.objects
        .filter(status="CONFIRMED", date__isnull=False, date__lt=agora)
        .select_related("patient", "professional", "consulta", "local_atendimento")
        .prefetch_related("appointment_procedures__procedure")
        .order_by("date")
    )
    for appointment in qs.iterator(chunk_size=100):
        try:
            limite = _horario_limite_finalizacao(appointment=appointment)
            if limite is None or agora < limite:
                continue

            consulta = _garantir_consulta_cliente_presente(appointment)
            if consulta is None:
                logger.warning(
                    "Auto-finalização (cliente presente): sem consulta appointment=%s",
                    appointment.id,
                )
                continue
            consulta.refresh_from_db()
            if consulta.status == "COMPLETED":
                if appointment.status != "COMPLETED":
                    appointment.status = "COMPLETED"
                    appointment.version = (appointment.version or 1) + 1
                    appointment.save(update_fields=["status", "version", "updated_at"])
                continue
            if consulta.status == "IN_PROGRESS":
                # Coberto pelo fluxo de em andamento
                continue
            if consulta.status not in _STATUS_CONSULTA_SEM_INICIAR:
                continue

            _finalizar_com_horario_agendado(consulta)
            total += 1
            logger.info(
                "Auto-finalização (cliente presente): appointment=%s consulta=%s "
                "paciente=%s slot=%s limite=%s",
                appointment.id,
                consulta.id,
                appointment.patient.nome if appointment.patient_id else "?",
                appointment.date.isoformat() if appointment.date else "?",
                limite.isoformat(),
            )
        except Exception as exc:
            logger.warning(
                "Auto-finalização (cliente presente) falhou: appointment=%s: %s",
                appointment.id, exc,
            )
    return total


def finalizar_consultas_esquecidas() -> int:
    """Finaliza consultas esquecidas (em andamento ou cliente presente sem iniciar).
    Retorna quantidade de consultas finalizadas.
    """
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    agora = timezone.now()
    total = 0

    for loja in _lojas_clinica_beleza():
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            total += _finalizar_em_andamento_esquecidas(agora)
            total += _finalizar_cliente_presente_sem_iniciar(agora)
        except Exception as exc:
            logger.exception("Auto-finalização loja %s: %s", loja.id, exc)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")

    if total:
        logger.info("Auto-finalização: %d consulta(s) finalizada(s) automaticamente", total)
    return total
