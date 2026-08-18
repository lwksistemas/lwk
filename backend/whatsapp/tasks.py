"""Tarefas agendadas para lembretes WhatsApp (ETAPA 4).
Executar no contexto de cada loja (tenant) para acessar Appointment/Patient.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

# Janela do lembrete 2h: precisa ser maior que o intervalo do job (15 min).
_JANELA_2H_ANTES = timedelta(hours=1, minutes=40)
_JANELA_2H_DEPOIS = timedelta(hours=2, minutes=20)
_CACHE_LEMBRETE_2H = 4 * 3600
_CACHE_LEMBRETE_24H = 26 * 3600
STATUS_LEMBRETE_CLINICA = (
    "SCHEDULED",
    "PENDING",
    "CONFIRMED",
    "CLIENT_CONFIRMED",
    "PHONE_CONFIRMED",
)


def _telefone_paciente(patient) -> str:
    """Paciente da clínica usa `telefone`; adapters/legado podem expor `phone`."""
    if patient is None:
        return ""
    return str(
        getattr(patient, "phone", None)
        or getattr(patient, "telefone", None)
        or ""
    ).strip()


def _paciente_aceita_whatsapp(patient) -> bool:
    if patient is None:
        return False
    if not getattr(patient, "allow_whatsapp", True):
        return False
    return bool(_telefone_paciente(patient))


def _reservar_lembrete(tipo: str, loja_id, appointment_id, timeout: int) -> str | None:
    """Evita reenvio no mesmo ciclo. Retorna a chave se esta chamada deve enviar."""
    from django.core.cache import cache

    key = f"wa_lembrete:{tipo}:{loja_id}:{appointment_id}"
    if cache.add(key, 1, timeout=timeout):
        return key
    return None


def _enviar_lembrete_unico(tipo, loja_id, appointment_id, agendamento, config, timeout: int) -> bool:
    from django.core.cache import cache
    from whatsapp.services import enviar_lembrete_agendamento

    key = _reservar_lembrete(tipo, loja_id, appointment_id, timeout)
    if not key:
        return False
    ok, _ = enviar_lembrete_agendamento(agendamento, user=None, config=config)
    if not ok:
        cache.delete(key)
        return False
    return True


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
    from whatsapp.confirmacao_agenda_service import SLUGS_CONFIRMACAO_AGENDA

    slugs = SLUGS_CONFIRMACAO_AGENDA - {"cabeleireiro"}
    return Loja.objects.filter(
        database_created=True,
        is_active=True,
        tipo_loja__slug__in=slugs,
    )


def _lojas_cabeleireiro_whatsapp():
    from superadmin.models import Loja

    return Loja.objects.filter(
        database_created=True,
        is_active=True,
        tipo_loja__slug="cabeleireiro",
    )


def _lojas_com_confirmacao_agenda_whatsapp():
    from superadmin.models import Loja
    from whatsapp.confirmacao_agenda_service import loja_usa_confirmacao_agenda

    return [
        loja
        for loja in Loja.objects.filter(
            database_created=True, is_active=True,
        ).select_related("tipo_loja")
        if loja_usa_confirmacao_agenda(loja)
    ]


def _send_lembretes_salao_24h():
    from cabeleireiro.models import Agendamento
    from cabeleireiro.whatsapp_agenda import SalaoAgendamentoWhatsAppAdapter
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    amanha = timezone.localdate() + timedelta(days=1)
    enviados = 0
    for loja in _lojas_cabeleireiro_whatsapp():
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_24h:
                continue
            qs = Agendamento.objects.filter(
                data=amanha,
                is_active=True,
                status__in=["SCHEDULED", "CLIENT_CONFIRMED"],
            ).select_related("cliente", "servico", "profissional")
            for ag in qs:
                if not getattr(ag.cliente, "allow_whatsapp", True):
                    continue
                if not (getattr(ag.cliente, "telefone", None) or "").strip():
                    continue
                if _enviar_lembrete_unico(
                    "24h", loja.id, ag.id, SalaoAgendamentoWhatsAppAdapter(ag),
                    config, _CACHE_LEMBRETE_24H,
                ):
                    enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 24h salão loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    return enviados


def _send_lembretes_salao_2h():
    from cabeleireiro.models import Agendamento
    from cabeleireiro.whatsapp_agenda import SalaoAgendamentoWhatsAppAdapter
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    now = timezone.localtime()
    inicio = now + _JANELA_2H_ANTES
    fim = now + _JANELA_2H_DEPOIS
    enviados = 0
    for loja in _lojas_cabeleireiro_whatsapp():
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_2h:
                continue
            # Filtra por data nos dias da janela e checa hora no Python
            datas = {inicio.date(), fim.date()}
            qs = Agendamento.objects.filter(
                data__in=datas,
                is_active=True,
                status__in=["SCHEDULED", "CLIENT_CONFIRMED"],
            ).select_related("cliente", "servico", "profissional")
            from datetime import datetime as dt_cls

            for ag in qs:
                if not getattr(ag.cliente, "allow_whatsapp", True):
                    continue
                if not (getattr(ag.cliente, "telefone", None) or "").strip():
                    continue
                naive = dt_cls.combine(ag.data, ag.hora_inicio)
                aware = timezone.make_aware(naive, timezone.get_current_timezone())
                if not (inicio <= aware <= fim):
                    continue
                if _enviar_lembrete_unico(
                    "2h", loja.id, ag.id, SalaoAgendamentoWhatsAppAdapter(ag),
                    config, _CACHE_LEMBRETE_2H,
                ):
                    enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 2h salão loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    return enviados


def send_lembretes_24h_whatsapp():
    """Envia lembrete por WhatsApp 24h antes do agendamento.
    Itera sobre lojas com database_created e configuração habilitada.
    """
    from clinica_beleza.models import Appointment
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    amanha = timezone.localdate() + timedelta(days=1)
    lojas = _lojas_clinica_beleza_whatsapp()
    enviados = 0
    for loja in lojas:
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_24h:
                continue
            qs = Appointment.objects.filter(
                date__date=amanha,
                status__in=STATUS_LEMBRETE_CLINICA,
            ).select_related("patient", "procedure")
            for ag in qs:
                if not _paciente_aceita_whatsapp(ag.patient):
                    continue
                if _enviar_lembrete_unico("24h", loja.id, ag.id, ag, config, _CACHE_LEMBRETE_24H):
                    enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 24h loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    enviados += _send_lembretes_salao_24h()
    logger.info("WhatsApp lembretes 24h: %d enviados", enviados)
    return enviados


def send_lembretes_2h_whatsapp():
    """Envia lembrete por WhatsApp ~2h antes do horário do agendamento.
    Janela: entre 1h40 e 2h20 a partir de agora (maior que o intervalo do job).
    """
    from clinica_beleza.models import Appointment
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    now = timezone.now()
    inicio = now + _JANELA_2H_ANTES
    fim = now + _JANELA_2H_DEPOIS
    lojas = _lojas_clinica_beleza_whatsapp()
    enviados = 0
    for loja in lojas:
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_lembrete_2h:
                continue
            qs = Appointment.objects.filter(
                date__gte=inicio,
                date__lte=fim,
                status__in=STATUS_LEMBRETE_CLINICA,
            ).select_related("patient", "procedure")
            for ag in qs:
                if not _paciente_aceita_whatsapp(ag.patient):
                    continue
                if _enviar_lembrete_unico("2h", loja.id, ag.id, ag, config, _CACHE_LEMBRETE_2H):
                    enviados += 1
        except Exception as e:
            logger.exception("WhatsApp lembrete 2h loja %s: %s", getattr(loja, "slug", loja.id), e)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    enviados += _send_lembretes_salao_2h()
    logger.info("WhatsApp lembretes 2h: %d enviados", enviados)
    return enviados


def _paciente_pode_receber_confirmacao(agendamento) -> bool:
    return _paciente_aceita_whatsapp(getattr(agendamento, "patient", None))


def _send_confirmacoes_clinica(config, hoje, inicio, fim):
    from clinica_beleza.agenda_confirmacao_service import STATUS_ACIONAVEIS
    from clinica_beleza.models import Appointment
    from whatsapp.confirmacao_agenda_service import processar_agendamento_hoje

    enviados = 0
    qs = Appointment.objects.filter(
        date__date__gte=inicio,
        date__date__lte=fim,
        status__in=list(STATUS_ACIONAVEIS),
    ).select_related("patient", "procedure", "professional")
    for ag in qs:
        if not _paciente_pode_receber_confirmacao(ag):
            continue
        enviados += processar_agendamento_hoje(ag, config=config, hoje=hoje)
    return enviados


def _send_confirmacoes_salao(config, hoje, inicio, fim):
    from cabeleireiro.models import Agendamento
    from cabeleireiro.whatsapp_agenda import (
        STATUS_ACIONAVEIS,
        SalaoAgendamentoWhatsAppAdapter,
    )
    from whatsapp.confirmacao_agenda_service import processar_agendamento_hoje

    enviados = 0
    qs = Agendamento.objects.filter(
        data__gte=inicio,
        data__lte=fim,
        is_active=True,
        status__in=list(STATUS_ACIONAVEIS),
    ).select_related("cliente", "servico", "profissional")
    for ag in qs:
        adapter = SalaoAgendamentoWhatsAppAdapter(ag)
        if not _paciente_pode_receber_confirmacao(adapter):
            continue
        enviados += processar_agendamento_hoje(adapter, config=config, hoje=hoje)
    return enviados


def send_confirmacoes_agendadas_whatsapp():
    """Envia o link de confirmação nos dias configurados (e última chance no mesmo dia)."""
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from whatsapp.confirmacao_agenda_service import (
        antecedencias_da_config,
        janela_datas,
    )

    hoje = timezone.localtime(timezone.now()).date()
    enviados = 0
    lojas = _lojas_com_confirmacao_agenda_whatsapp()
    vistos = set()
    for loja in lojas:
        if loja.id in vistos:
            continue
        vistos.add(loja.id)
        try:
            db_name = _ensure_loja_db(loja)
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            config = _get_whatsapp_config(loja)
            if not config or not config.whatsapp_ativo or not config.enviar_confirmacao:
                continue
            antecedencias = antecedencias_da_config(config)
            janela = janela_datas(antecedencias, hoje=hoje)
            if not janela:
                continue
            inicio, fim = janela
            tipo = getattr(getattr(loja, "tipo_loja", None), "slug", "") or ""
            if tipo == "cabeleireiro":
                enviados += _send_confirmacoes_salao(config, hoje, inicio, fim)
            else:
                enviados += _send_confirmacoes_clinica(config, hoje, inicio, fim)
        except Exception as e:
            logger.exception(
                "WhatsApp confirmação agendada loja %s: %s",
                getattr(loja, "slug", loja.id), e,
            )
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    logger.info("WhatsApp confirmações agendadas: %d enviados", enviados)
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
