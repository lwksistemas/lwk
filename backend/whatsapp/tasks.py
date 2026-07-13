"""Tarefas agendadas para lembretes WhatsApp (ETAPA 4).
Executar no contexto de cada loja (tenant) para acessar Appointment/Patient.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


def _ensure_loja_db(loja):
    """Garante que o banco da loja está em DATABASES (para workers sem request)."""
    from core.db_config import ensure_loja_database_config
    db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", loja.id)}'.replace("-", "_")
    ensure_loja_database_config(db_name, conn_max_age=0)
    return db_name


def _get_whatsapp_config(loja):
    """Retorna WhatsAppConfig da loja ou None. Chamar com contexto tenant já setado (tabela isolada por loja)."""
    from whatsapp.models import WhatsAppConfig
    try:
        return WhatsAppConfig.objects.filter(loja=loja).first()
    except Exception:
        return None


def _lojas_clinica_beleza_whatsapp():
    from superadmin.models import Loja

    return Loja.objects.filter(
        database_created=True,
        is_active=True,
        tipo_loja__slug="clinica-beleza",
    )


def send_lembretes_24h_whatsapp():
    """Envia lembrete por WhatsApp 24h antes do agendamento.
    Itera sobre lojas com database_created e configuração habilitada.
    """
    from clinica_beleza.models import Appointment
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from whatsapp.services import enviar_lembrete_agendamento

    amanha = (timezone.now() + timedelta(days=1)).date()
    lojas = _lojas_clinica_beleza_whatsapp()
    enviados = 0
    for loja in lojas:
        try:
            from tenants.middleware import set_current_loja_id, set_current_tenant_db
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_24h:
                continue
            # Agendamentos de amanhã (status confirmado/agendado)
            qs = Appointment.objects.filter(
                date__date=amanha,
                status__in=["CONFIRMED", "CLIENT_CONFIRMED", "PHONE_CONFIRMED", "SCHEDULED"],
            ).select_related("patient", "procedure")
            for ag in qs:
                if not getattr(ag.patient, "allow_whatsapp", True):
                    continue
                if getattr(ag.patient, "phone", None):
                    ok, _ = enviar_lembrete_agendamento(ag, user=None, config=config)
                    if ok:
                        enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 24h loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    logger.info("WhatsApp lembretes 24h: %d enviados", enviados)
    return enviados


def send_lembretes_2h_whatsapp():
    """Envia lembrete por WhatsApp ~2h antes do horário do agendamento.
    Janela: entre 1h50 e 2h10 a partir de agora.
    """
    from clinica_beleza.models import Appointment
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from whatsapp.services import enviar_lembrete_agendamento

    now = timezone.now()
    inicio = now + timedelta(hours=1, minutes=50)
    fim = now + timedelta(hours=2, minutes=10)
    lojas = _lojas_clinica_beleza_whatsapp()
    enviados = 0
    for loja in lojas:
        try:
            from tenants.middleware import set_current_loja_id, set_current_tenant_db
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_2h:
                continue
            # Agendamentos na janela 2h
            qs = Appointment.objects.filter(
                date__gte=inicio,
                date__lte=fim,
                status__in=["CONFIRMED", "CLIENT_CONFIRMED", "PHONE_CONFIRMED", "SCHEDULED"],
            ).select_related("patient", "procedure")
            for ag in qs:
                if not getattr(ag.patient, "allow_whatsapp", True):
                    continue
                if getattr(ag.patient, "phone", None):
                    ok, _ = enviar_lembrete_agendamento(ag, user=None, config=config)
                    if ok:
                        enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 2h loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    logger.info("WhatsApp lembretes 2h: %d enviados", enviados)
    return enviados


def send_cobrancas_pendentes_whatsapp():
    """Envia cobrança por WhatsApp para pacientes com pagamento PENDING.
    Uma mensagem por paciente/dia (agrupa débitos). Só lojas Clínica da Beleza.
    """
    from clinica_beleza.models import Payment
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from whatsapp.models import WhatsAppLog
    from whatsapp.services import enviar_cobranca_whatsapp

    hoje = timezone.localtime(timezone.now()).date()
    lojas = Loja.objects.filter(
        database_created=True,
        is_active=True,
        tipo_loja__slug="clinica-beleza",
    )
    enviados = 0
    for loja in lojas:
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_cobranca:
                continue

            pendentes = (
                Payment.objects.filter(status="PENDING")
                .select_related("appointment__patient")
                .order_by("-created_at")
            )
            por_paciente = {}
            for pay in pendentes:
                patient = getattr(pay.appointment, "patient", None)
                if not patient or not getattr(patient, "allow_whatsapp", True):
                    continue
                phone = (getattr(patient, "phone", None) or "").strip()
                if not phone:
                    continue
                pid = patient.id
                if pid not in por_paciente:
                    por_paciente[pid] = {"patient": patient, "total": 0}
                por_paciente[pid]["total"] += float(pay.amount or 0)

            for item in por_paciente.values():
                patient = item["patient"]
                phone = (getattr(patient, "phone", None) or "").strip()
                ja_enviou = WhatsAppLog.objects.using(db_name).filter(
                    loja_id=loja.id,
                    telefone__icontains=phone[-8:],
                    created_at__date=hoje,
                    mensagem__icontains="pagamento pendente",
                ).exists()
                if ja_enviou:
                    continue
                ok, _ = enviar_cobranca_whatsapp(
                    patient, item["total"], user=None, config=config,
                )
                if ok:
                    enviados += 1
        except Exception as e:
            logger.exception(
                "WhatsApp cobrança loja %s: %s", getattr(loja, "slug", loja.id), e,
            )
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    logger.info("WhatsApp cobranças pendentes: %d enviados", enviados)
    return enviados
