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
    """
    Remove tudo que não for dígito. Retorna número em formato internacional (com código do país).
    Meta Cloud API exige "to" com código do país, sem + (ex.: 5511999999999, 15551779791).
    """
    if not telefone:
        return None
    digits = re.sub(r'\D', '', str(telefone))
    if len(digits) < 10:
        return None
    # Já tem código do país (12–15 dígitos): usar como está (remover zero à esquerda após 55)
    if len(digits) >= 12:
        out = digits[:15]
        if out.startswith('55') and len(out) > 12 and out[2] == '0':
            out = '55' + out[3:].lstrip('0')  # ex.: 55016981402966 → 5516981402966
        return out
    # 11 dígitos: EUA (1 + 10) usar como está; Brasil (DDD + 9 dígitos) → adicionar 55
    if len(digits) == 11:
        if digits.startswith('1'):
            return digits
        # Remove zero à esquerda (ex.: 016981402966 → 5516981402966)
        br = digits.lstrip('0')
        if len(br) < 10:
            return None
        return '55' + br
    # 10 dígitos: assumir Brasil (DDD 2 + 8 dígitos)
    if len(digits) == 10:
        return '55' + digits.lstrip('0') if digits.lstrip('0') else '55' + digits
    return digits[:15]


def send_whatsapp_document(telefone, document_url, filename, caption=None, user=None, config=None):
    """
    Envia documento (PDF) via WhatsApp Cloud API.
    document_url: URL pública HTTPS do documento (Meta precisa conseguir baixar).
    filename: nome do arquivo (ex: proposta.pdf)
    caption: legenda opcional (máx 1024 caracteres)
    Retorna (True, None) ou (False, mensagem_erro).
    """
    phone = _normalize_phone(telefone)
    loja = config.loja if config else None
    if not phone:
        logger.warning("WhatsApp documento: telefone inválido: %s", telefone)
        WhatsAppLog.objects.create(
            loja=loja,
            user=user,
            telefone=telefone or '',
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': 'telefone_invalido'},
        )
        return False, "Telefone inválido ou incompleto."

    api_url = getattr(settings, 'WHATSAPP_API_URL', None) or 'https://graph.facebook.com/v19.0'
    phone_id = None
    token = None
    if config and getattr(config, 'whatsapp_ativo', False):
        phone_id = (getattr(config, 'whatsapp_phone_id', None) or '').strip()
        token = (getattr(config, 'whatsapp_token', None) or '').strip()
    if not phone_id or not token:
        phone_id = phone_id or getattr(settings, 'WHATSAPP_PHONE_ID', None)
        token = token or getattr(settings, 'WHATSAPP_TOKEN', None)

    if not phone_id or not token:
        WhatsAppLog.objects.create(
            loja=loja,
            user=user,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': 'config_missing'},
        )
        return False, "Phone Number ID e Token não configurados. Configure em Configurações → WhatsApp."

    url = f"{api_url.rstrip('/')}/{phone_id}/messages"
    doc_payload = {"link": document_url, "filename": filename}
    if caption:
        doc_payload["caption"] = str(caption)[:1024]
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "document",
        "document": doc_payload,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
    except Exception as e:
        logger.exception("WhatsApp documento: erro de requisição")
        WhatsAppLog.objects.create(
            loja=loja,
            user=user,
            telefone=phone,
            mensagem=f"[documento] {filename}",
            status='falhou',
            response={'error': str(e)},
        )
        return False, f"Erro de conexão: {str(e)}"

    ok = response.ok and bool(data.get('messages'))
    WhatsAppLog.objects.create(
        loja=loja,
        user=user,
        telefone=phone,
        mensagem=f"[documento] {filename}",
        status='enviado' if ok else 'falhou',
        response=data,
    )
    if ok:
        return True, None
    err = data.get('error') or {}
    msg = (err.get('message') or err.get('error_user_msg') or '').strip()
    return False, msg or "Erro ao enviar documento pelo WhatsApp."


def send_whatsapp(telefone, mensagem, user=None, config=None):
    """
    Envia mensagem de texto via WhatsApp Cloud API.
    Se config (WhatsAppConfig da loja) for passado e estiver ativo, usa número/token da loja.
    Caso contrário usa variáveis globais WHATSAPP_PHONE_ID/WHATSAPP_TOKEN (fallback).
    Registra em WhatsAppLog (auditoria por loja).
    Retorna (True, None) se enviou com sucesso; (False, mensagem_erro) em caso de falha.
    """
    phone = _normalize_phone(telefone)
    loja = config.loja if config else None
    if not phone:
        logger.warning("WhatsApp: telefone inválido ou vazio: %s", telefone)
        WhatsAppLog.objects.create(
            loja=loja,
            user=user,
            telefone=telefone or '',
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': 'telefone_invalido'},
        )
        return False, "Telefone inválido ou incompleto (use DDD + número com código do país)."

    api_url = getattr(settings, 'WHATSAPP_API_URL', None) or 'https://graph.facebook.com/v19.0'
    phone_id = None
    token = None
    if config and getattr(config, 'whatsapp_ativo', False):
        phone_id = (getattr(config, 'whatsapp_phone_id', None) or '').strip()
        token = (getattr(config, 'whatsapp_token', None) or '').strip()
    if not phone_id or not token:
        phone_id = phone_id or getattr(settings, 'WHATSAPP_PHONE_ID', None)
        token = token or getattr(settings, 'WHATSAPP_TOKEN', None)

    if not phone_id or not token:
        logger.warning(
            "WhatsApp: phone_id/token não configurados (loja nem WHATSAPP_PHONE_ID/WHATSAPP_TOKEN). "
            "Configure a API do WhatsApp Business (Meta) para enviar mensagens."
        )
        WhatsAppLog.objects.create(
            loja=loja,
            user=user,
            telefone=phone,
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': 'config_missing'},
        )
        return False, "Phone Number ID e Token não configurados. Preencha em Configurações → WhatsApp."

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
            loja=loja,
            user=user,
            telefone=phone,
            mensagem=mensagem[:500],
            status='falhou',
            response={'error': str(e)},
        )
        return False, f"Erro de conexão: {str(e)}"

    # Sucesso só quando a Meta devolve o id da mensagem (messages não vazio)
    ok = response.ok and bool(data.get('messages'))
    if response.ok and not ok:
        logger.warning("WhatsApp: Meta respondeu %s mas sem 'messages' na resposta: %s", response.status_code, data)
    WhatsAppLog.objects.create(
        loja=loja,
        user=user,
        telefone=phone,
        mensagem=mensagem[:500],
        status='enviado' if ok else 'falhou',
        response=data,
    )
    if ok:
        return True, None
    # Erro da API Meta: ex.: invalid phone_number_id, token expirado, recipient não elegível
    err = data.get('error') or {}
    code = err.get('code')
    msg = (err.get('message') or err.get('error_user_msg') or '').strip()
    if not msg and isinstance(err.get('error_data'), dict):
        msg = (err['error_data'].get('details') or '').strip()
    # Mensagem amigável para erro de "lista de permitidos" (app em modo teste)
    if msg and 'not in allowed list' in msg.lower():
        detail = (
            "O número do paciente não está na lista de números permitidos da Meta. "
            "Com o app em modo de teste, só é possível enviar para números cadastrados. "
            "Em developers.facebook.com → seu app → WhatsApp → API Setup, adicione o número do paciente em \"To\" (números de teste)."
        )
    else:
        detail = msg or (f"Erro da API Meta (código {code})" if code else "Resposta inesperada da API Meta.")
    return False, detail


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

def enviar_confirmacao_agendamento(agendamento, user=None, config=None):
    """
    Envia confirmação por WhatsApp ao paciente.
    Chamar quando o agendamento for confirmado. Passar config da loja para usar número/token da clínica.
    Retorna (True, None) ou (False, mensagem_erro).
    """
    phone = getattr(agendamento.patient, 'phone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."
    msg = msg_confirmacao(agendamento)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)


def enviar_lembrete_agendamento(agendamento, user=None, config=None):
    """Envia lembrete por WhatsApp (ex.: dia do atendimento). Passar config da loja. Retorna (ok, erro)."""
    phone = getattr(agendamento.patient, 'phone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."
    msg = msg_lembrete(agendamento)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)


def enviar_cobranca_whatsapp(paciente, valor, user=None, config=None):
    """Envia mensagem de cobrança por WhatsApp. Passar config da loja. Retorna (ok, erro)."""
    phone = getattr(paciente, 'phone', None)
    if not phone:
        return False, "Paciente sem telefone cadastrado."
    msg = msg_cobranca(paciente, valor)
    return send_whatsapp(telefone=phone, mensagem=msg, user=user, config=config)
