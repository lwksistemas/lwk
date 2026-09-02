"""Auto-finalização de consultas esquecidas em andamento (IN_PROGRESS).

Regra: 5 horas após o fim do agendamento (início + duração efetiva).
Roda a cada 15 min no worker Django-Q e no cron LWK.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

MARGEM_APOS_FIM_AGENDAMENTO_HORAS = 5


def _lojas_clinica_beleza():
    from .catalogo_service import lojas_clinica_beleza_com_schema

    return lojas_clinica_beleza_com_schema(apenas_ativas=True)


def _fim_agendamento(consulta):
    """Fim previsto do horário agendado: data do appointment + duração efetiva."""
    appointment = getattr(consulta, "appointment", None)
    inicio = None
    if appointment is not None:
        inicio = getattr(appointment, "date", None)
    if inicio is None:
        inicio = getattr(consulta, "data_inicio", None)
    if inicio is None:
        return None
    duracao = 30
    if appointment is not None and hasattr(appointment, "get_duracao_efetiva"):
        try:
            duracao = int(appointment.get_duracao_efetiva() or 30)
        except Exception:
            duracao = 30
    if duracao < 1:
        duracao = 30
    return inicio + timedelta(minutes=duracao)


def _horario_limite_finalizacao(consulta) -> timezone.datetime | None:
    """Horário em que a consulta pode ser auto-finalizada (fim do agendamento + 5h)."""
    fim = _fim_agendamento(consulta)
    if fim is None:
        return None
    return fim + timedelta(hours=MARGEM_APOS_FIM_AGENDAMENTO_HORAS)


def finalizar_consultas_esquecidas() -> int:
    """Finaliza automaticamente consultas IN_PROGRESS que ultrapassaram o tempo limite.
    Retorna quantidade de consultas finalizadas.
    """
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .consulta_service import finalizar_consulta
    from .models import Consulta

    agora = timezone.now()
    total = 0

    for loja in _lojas_clinica_beleza():
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)

            consultas_em_andamento = (
                Consulta.objects
                .filter(status="IN_PROGRESS", data_inicio__isnull=False)
                .select_related("appointment", "appointment__professional", "patient")
                .prefetch_related("appointment__appointment_procedures__procedure")
            )

            for consulta in consultas_em_andamento.iterator(chunk_size=100):
                try:
                    limite = _horario_limite_finalizacao(consulta)
                    if limite is None or agora < limite:
                        continue

                    finalizar_consulta(consulta, skip_estoque=True)
                    total += 1
                    logger.info(
                        "Auto-finalização: consulta=%s loja=%s paciente=%s "
                        "(início=%s, limite=%s)",
                        consulta.id, loja.id,
                        consulta.patient.nome if consulta.patient_id else "?",
                        consulta.data_inicio.isoformat() if consulta.data_inicio else "?",
                        limite.isoformat(),
                    )
                except Exception as exc:
                    logger.warning(
                        "Auto-finalização falhou: consulta=%s loja=%s: %s",
                        consulta.id, loja.id, exc,
                    )
        except Exception as exc:
            logger.exception("Auto-finalização loja %s: %s", loja.id, exc)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")

    if total:
        logger.info("Auto-finalização: %d consulta(s) finalizada(s) automaticamente", total)
    return total
