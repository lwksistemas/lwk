"""
Tarefas agendadas para lembretes WhatsApp (ETAPA 4).
Executar no contexto de cada loja (tenant) para acessar Appointment/Patient.
"""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_whatsapp_config(loja):
    """Retorna WhatsAppConfig da loja ou None (usa defaults se não existir)."""
    try:
        return loja.whatsapp_config
    except Exception:
        return None


def send_lembretes_24h_whatsapp():
    """
    Envia lembrete por WhatsApp 24h antes do agendamento.
    Itera sobre lojas com database_created e configuração habilitada.
    """
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from clinica_beleza.models import Appointment
    from whatsapp.services import enviar_lembrete_agendamento

    amanha = (timezone.now() + timedelta(days=1)).date()
    lojas = Loja.objects.filter(database_created=True, is_active=True)
    enviados = 0
    for loja in lojas:
        try:
            config = _get_whatsapp_config(loja)
            if config and not config.enviar_lembrete_24h:
                continue
            set_current_loja_id(loja.id)
            set_current_tenant_db(loja.database_name)
            # Agendamentos de amanhã (status confirmado/agendado)
            qs = Appointment.objects.filter(
                date__date=amanha,
                status__in=['CONFIRMED', 'SCHEDULED'],
            ).select_related('patient', 'procedure')
            for ag in qs:
                if not getattr(ag.patient, 'allow_whatsapp', True):
                    continue
                if getattr(ag.patient, 'phone', None):
                    if enviar_lembrete_agendamento(ag, user=None):
                        enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 24h loja %s: %s", getattr(loja, 'slug', loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db('default')
    logger.info("WhatsApp lembretes 24h: %d enviados", enviados)
    return enviados


def send_lembretes_2h_whatsapp():
    """
    Envia lembrete por WhatsApp ~2h antes do horário do agendamento.
    Janela: entre 1h50 e 2h10 a partir de agora.
    """
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from clinica_beleza.models import Appointment
    from whatsapp.services import enviar_lembrete_agendamento

    now = timezone.now()
    inicio = now + timedelta(hours=1, minutes=50)
    fim = now + timedelta(hours=2, minutes=10)
    lojas = Loja.objects.filter(database_created=True, is_active=True)
    enviados = 0
    for loja in lojas:
        try:
            config = _get_whatsapp_config(loja)
            if config and not config.enviar_lembrete_2h:
                continue
            set_current_loja_id(loja.id)
            set_current_tenant_db(loja.database_name)
            qs = Appointment.objects.filter(
                date__gte=inicio,
                date__lte=fim,
                status__in=['CONFIRMED', 'SCHEDULED'],
            ).select_related('patient', 'procedure')
            for ag in qs:
                if not getattr(ag.patient, 'allow_whatsapp', True):
                    continue
                if getattr(ag.patient, 'phone', None):
                    if enviar_lembrete_agendamento(ag, user=None):
                        enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 2h loja %s: %s", getattr(loja, 'slug', loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db('default')
    logger.info("WhatsApp lembretes 2h: %d enviados", enviados)
    return enviados
