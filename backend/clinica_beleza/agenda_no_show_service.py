"""
Marca agendamentos como Faltou (NO_SHOW) quando passam 2h do horário sem chegada.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

NO_SHOW_HORAS = 2
_STATUS_ELEGIVEL_FALTA = frozenset({
    'SCHEDULED', 'PENDING', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED',
})


def _lojas_clinica_beleza():
    from superadmin.models import Loja

    return (
        Loja.objects.using('default')
        .select_related('tipo_loja')
        .filter(is_active=True, database_created=True, tipo_loja__nome='Clínica da Beleza')
    )


def marcar_faltas_agenda_automatico() -> int:
    """
    Atualiza agendamentos elegíveis para NO_SHOW.
    Retorna quantidade de registros alterados.
    """
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .agenda_service import atualizar_agendamento
    from .models import Appointment

    limite = timezone.now() - timedelta(hours=NO_SHOW_HORAS)
    total = 0

    for loja in _lojas_clinica_beleza():
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            qs = (
                Appointment.objects
                .filter(status__in=_STATUS_ELEGIVEL_FALTA, date__lt=limite)
                .order_by('date')
            )
            for appointment in qs.iterator():
                try:
                    atualizar_agendamento(appointment, new_status='NO_SHOW', user=None, request=None)
                    total += 1
                except Exception as exc:
                    logger.warning(
                        'NO_SHOW automático falhou loja=%s agendamento=%s: %s',
                        loja.id, appointment.id, exc,
                    )
        except Exception as exc:
            logger.exception('NO_SHOW automático loja %s: %s', loja.id, exc)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db('default')

    if total:
        logger.info('NO_SHOW automático: %d agendamento(s) marcado(s) como faltou', total)
    return total
