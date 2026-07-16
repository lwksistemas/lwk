"""Auto-finalização de consultas esquecidas em andamento (IN_PROGRESS).

Regras:
- Consulta SEM procedimentos: finaliza após o término previsto + margem.
- Consulta COM procedimentos: finaliza após o término previsto + margem maior.
- Nunca finaliza se houve atividade recente na consulta (updated_at).

Roda a cada 15 min via cron (executar_cron_lwks).
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

# Margem após o fim previsto (atendimentos longos / multi-procedimento)
MARGEM_SEM_PROCEDIMENTO_HORAS = 4
MARGEM_COM_PROCEDIMENTO_HORAS = 8
# Se o profissional ainda edita a consulta, não auto-finaliza
INATIVIDADE_MINIMA_HORAS = 3


def _lojas_clinica_beleza():
    from superadmin.models import Loja

    return (
        Loja.objects.using("default")
        .select_related("tipo_loja")
        .filter(is_active=True, database_created=True, tipo_loja__nome="Clínica da Beleza")
    )


def _consulta_tem_procedimentos(consulta) -> bool:
    """Verifica se a consulta/appointment tem procedimentos associados."""
    appointment = consulta.appointment
    return bool(appointment.appointment_procedures.exists() or appointment.procedure_id)


def _horario_limite_finalizacao(consulta) -> timezone.datetime:
    """Calcula o horário limite para auto-finalização:
    - data_inicio + duração efetiva + margem de tolerância.
    """
    if not consulta.data_inicio:
        return None

    appointment = consulta.appointment
    duracao_efetiva = appointment.get_duracao_efetiva()

    tem_procedimentos = _consulta_tem_procedimentos(consulta)
    margem_horas = MARGEM_COM_PROCEDIMENTO_HORAS if tem_procedimentos else MARGEM_SEM_PROCEDIMENTO_HORAS

    fim_previsto = consulta.data_inicio + timedelta(minutes=duracao_efetiva)
    limite = fim_previsto + timedelta(hours=margem_horas)
    return limite


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

            # Django exige chunk_size quando iterator() é usado com prefetch_related()
            for consulta in consultas_em_andamento.iterator(chunk_size=100):
                try:
                    limite = _horario_limite_finalizacao(consulta)
                    if limite is None:
                        continue
                    if agora < limite:
                        continue
                    # Atividade recente (evolução, produtos, etc.) → ainda em uso
                    ref_atividade = consulta.updated_at or consulta.data_inicio
                    if ref_atividade and (agora - ref_atividade) < timedelta(hours=INATIVIDADE_MINIMA_HORAS):
                        continue

                    # Auto-finalizar a consulta (pula verificação de estoque)
                    finalizar_consulta(consulta, skip_estoque=True)
                    total += 1
                    logger.info(
                        "Auto-finalização: consulta=%s loja=%s paciente=%s "
                        "(início=%s, limite=%s)",
                        consulta.id, loja.id,
                        consulta.patient.nome if consulta.patient_id else "?",
                        consulta.data_inicio.isoformat(),
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
