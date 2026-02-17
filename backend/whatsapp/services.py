"""
Serviço de envio WhatsApp (Meta Cloud API) e templates de mensagem (ETAPA 4).
"""
import re
import logging
import requests
from django.conf import settings

from .models import WhatsAppLog

logger = logging.getLogger(__name__)


def _normalize_phone(telefone):
    """Remove tudo que não for dígito; exige DDD (11 dígitos para celular)."""
    if not telefone:
        return None
    digits = re.sub(r'\D', '', str(telefone))
    if len(digits) >= 10:
        return digits[-11:] if len(digits) > 11 else digits  # Brasil: 55 + DDD + 9 + 8 dígitos
    return None


def send_whatsapp(telefone, mensagem, user=None):
    """
    Envia mensagem de texto via WhatsApp Cloud API.
    Registra em WhatsAppLog (auditoria). Retorna True se enviou com sucesso.
    """
    phone = _normalize_phone(telefone)
    if not phone:
        logger.warning("WhatsApp: telefone inválido ou vazio: %s", telefone)
        WhatsAppLog.objects.create(
            user=user,
            telefone=telefone or '',
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': 'telefone_invalido'},
        )
        return False

    api_url = getattr(settings, 'WHATSAPP_API_URL', None) or 'https://graph.facebook.com/v19.0'
    phone_id = getattr(settings, 'WHATSAPP_PHONE_ID', None)
    token = getattr(settings, 'WHATSAPP_TOKEN', None)

    if not phone_id or not token:
        logger.warning("WhatsApp: WHATSAPP_PHONE_ID ou WHATSAPP_TOKEN não configurados")
        WhatsAppLog.objects.create(
            user=user,
            telefone=phone,
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': 'config_missing'},
        )
        return False

    url = f"{api_url.rstrip('/')}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": mensagem[:4096]},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
    except Exception as e:
        logger.exception("WhatsApp: erro de requisição")
        WhatsAppLog.objects.create(
            user=user,
            telefone=phone,
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': str(e)},
        )
        return False

    ok = response.ok and (data.get('messages') or not data.get('error'))
    WhatsAppLog.objects.create(
        user=user,
        telefone=phone,
        mensagem=mensagem[:500],
        status='enviado' if ok else 'falhou',
        response=data,
    )
    return ok


# --- Templates de mensagem (padrão clínica) ---

def msg_confirmacao(agendamento):
    """Confirmação de agendamento."""
    data = agendamento.date.strftime('%d/%m/%Y')
    hora = agendamento.date.strftime('%H:%M')
    nome = getattr(agendamento.patient, 'name', '') or 'Cliente'
    procedimento = getattr(agendamento.procedure, 'name', '') or 'Atendimento'
    return (
        f"Olá {nome} 😊\n\n"
        f"Seu horário foi confirmado:\n"
        f"📅 {data}\n"
        f"⏰ {hora}\n"
        f"💆 {procedimento}\n\n"
        f"Qualquer dúvida, fale conosco."
    )


def msg_lembrete(agendamento):
    """Lembrete de atendimento (ex.: dia do atendimento)."""
    hora = agendamento.date.strftime('%H:%M')
    return (
        f"Lembrete ⏰\n\n"
        f"Você tem atendimento hoje às {hora}.\n"
        f"Estamos te aguardando 😊"
    )


def msg_cobranca(paciente, valor):
    """Cobrança / pagamento pendente."""
    nome = getattr(paciente, 'name', '') or 'Cliente'
    valor_str = f"{float(valor):.2f}".replace('.', ',')
    return (
        f"Olá {nome} 💳\n\n"
        f"Identificamos um pagamento pendente no valor de R$ {valor_str}.\n"
        f"Qualquer dúvida, fale conosco."
    )


# --- Integração com agendamentos (chamar ao confirmar / lembrete / cobrança) ---

def enviar_confirmacao_agendamento(agendamento, user=None):
    """
    Envia confirmação por WhatsApp ao paciente.
    Chamar quando o agendamento for confirmado.
    """
    phone = getattr(agendamento.patient, 'phone', None)
    if not phone:
        return False
    msg = msg_confirmacao(agendamento)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user)


def enviar_lembrete_agendamento(agendamento, user=None):
    """Envia lembrete por WhatsApp (ex.: dia do atendimento)."""
    phone = getattr(agendamento.patient, 'phone', None)
    if not phone:
        return False
    msg = msg_lembrete(agendamento)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user)


def enviar_cobranca_whatsapp(paciente, valor, user=None):
    """Envia mensagem de cobrança por WhatsApp."""
    phone = getattr(paciente, 'phone', None)
    if not phone:
        return False
    msg = msg_cobranca(paciente, valor)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user)
