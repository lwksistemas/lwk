"""
Cliente HTTP para Evolution API (WhatsApp Web / Baileys).
Documentação: https://doc.evolution-api.com/
"""
import logging
import re
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EvolutionAPIError(Exception):
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


def evolution_configured():
    url = (getattr(settings, 'EVOLUTION_API_URL', None) or '').strip()
    key = (getattr(settings, 'EVOLUTION_API_KEY', None) or '').strip()
    return bool(url and key)


def evolution_instance_name(loja_id):
    return f'lwk_loja_{int(loja_id)}'


def _base_url():
    url = (getattr(settings, 'EVOLUTION_API_URL', None) or '').strip().rstrip('/')
    if not url:
        raise EvolutionAPIError('Evolution API não configurada (EVOLUTION_API_URL).')
    return url


def _headers():
    key = (getattr(settings, 'EVOLUTION_API_KEY', None) or '').strip()
    if not key:
        raise EvolutionAPIError('Evolution API key não configurada (EVOLUTION_API_KEY).')
    return {'apikey': key, 'Content-Type': 'application/json'}


def _request(method, path, json_body=None, timeout=30):
    url = f'{_base_url()}{path}'
    try:
        response = requests.request(method, url, headers=_headers(), json=json_body, timeout=timeout)
    except requests.RequestException as exc:
        logger.exception('Evolution API: erro de rede %s %s', method, path)
        raise EvolutionAPIError(f'Erro de conexão com Evolution API: {exc}') from exc
    data = {}
    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            data = response.json()
        except ValueError:
            data = {}
    if not response.ok:
        msg = _extract_error_message(data) or f'Evolution API respondeu HTTP {response.status_code}'
        raise EvolutionAPIError(msg, status_code=response.status_code, response=data)
    return data


def _extract_error_message(data):
    if not isinstance(data, dict):
        return None
    for key in ('message', 'error', 'response'):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, list) and val:
            parts = []
            for item in val:
                if isinstance(item, str) and item.strip():
                    parts.append(item.strip())
                elif isinstance(item, dict):
                    nested = item.get('message') or item.get('error')
                    if isinstance(nested, str) and nested.strip():
                        parts.append(nested.strip())
                    elif item.get('exists') is False:
                        jid = item.get('jid') or item.get('number') or ''
                        parts.append(
                            f'Número não encontrado no WhatsApp ({jid}). '
                            'Confira o telefone do paciente (DDD + número com 9 dígitos).'
                        )
            if parts:
                return ' '.join(parts)
        if isinstance(val, dict):
            nested = val.get('message') or val.get('error')
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
            if isinstance(nested, list) and nested:
                return _extract_error_message({'message': nested})
    return None


def _format_evolution_number(number):
    return re.sub(r'\D', '', str(number or ''))


def _candidate_whatsapp_numbers(number):
    """
    Variações do telefone para consulta na Evolution (BR: +55, 9º dígito).
    Entrada já pode vir normalizada de services._normalize_phone.
    """
    digits = _format_evolution_number(number)
    if not digits:
        return []

    candidates = [digits]

    if len(digits) == 11 and not digits.startswith('1'):
        candidates.append('55' + digits.lstrip('0'))
    elif len(digits) == 10:
        candidates.append('55' + digits.lstrip('0'))

    for value in list(candidates):
        if value.startswith('55') and len(value) == 12:
            candidates.append(value[:4] + '9' + value[4:])

    seen = set()
    ordered = []
    for value in candidates:
        if value not in seen and len(value) >= 10:
            seen.add(value)
            ordered.append(value)
    return ordered


def _prefer_br_mobile_digits(queried: str, resolved: str) -> str:
    """
    Evolution/Baileys às vezes devolve JID sem o 9º dígito do celular BR.
    Ex.: consulta 5562999792267 → retorna 556299792267.
    """
    q = _format_evolution_number(queried)
    r = _format_evolution_number(resolved)
    if (
        len(q) == 13
        and q.startswith('55')
        and q[4] == '9'
        and len(r) == 12
        and r.startswith('55')
        and r == q[:4] + q[5:]
    ):
        return q
    return r or q


def _lookup_whatsapp_number(instance_name, digits):
    data = _request('POST', f'/chat/whatsappNumbers/{instance_name}', json_body={'numbers': [digits]})
    if not isinstance(data, list) or not data:
        return None
    item = data[0]
    if not isinstance(item, dict) or not item.get('exists'):
        return None
    jid = (item.get('jid') or '').strip()
    resolved = _digits_from_jid(jid) if jid else ''
    resolved = resolved or _format_evolution_number(item.get('number') or digits)
    return _prefer_br_mobile_digits(digits, resolved)


def _pick_best_resolved_number(input_digits: str, matches: list[tuple[str, str]]) -> str:
    """Escolhe o melhor número entre candidatos válidos (prioriza entrada e celular BR com 9)."""
    if not matches:
        return ''
    input_digits = _format_evolution_number(input_digits)

    for candidate, resolved in matches:
        if _format_evolution_number(resolved) == input_digits:
            return _prefer_br_mobile_digits(candidate, resolved)
        if _format_evolution_number(candidate) == input_digits:
            return _prefer_br_mobile_digits(candidate, resolved)

    for candidate, resolved in matches:
        preferred = _prefer_br_mobile_digits(candidate, resolved)
        if len(preferred) == 13 and preferred.startswith('55') and preferred[4] == '9':
            return preferred

    candidate, resolved = matches[0]
    return _prefer_br_mobile_digits(candidate, resolved)


def resolve_recipient_number(instance_name, number):
    """
    Confirma na Evolution se o número existe no WhatsApp e retorna digits normalizados.
    """
    input_digits = _format_evolution_number(number)
    candidates = _candidate_whatsapp_numbers(number)
    if not candidates:
        raise EvolutionAPIError(
            'Telefone inválido para envio via WhatsApp Web. '
            'Use DDD + número (ex: 16999998888 ou 5516999999999).'
        )

    matches: list[tuple[str, str]] = []
    for candidate in candidates:
        try:
            resolved = _lookup_whatsapp_number(instance_name, candidate)
        except EvolutionAPIError:
            continue
        if resolved:
            matches.append((candidate, resolved))

    if matches:
        return _pick_best_resolved_number(input_digits, matches)

    tried = ', '.join(candidates[:3])
    raise EvolutionAPIError(
        f'Número não encontrado no WhatsApp ({tried}). '
        'Confira o telefone — use celular com WhatsApp ativo, DDD e 9 dígitos.'
    )


def evolution_send_error_message(exc: 'EvolutionAPIError') -> str:
    """Mensagem amigável para falhas de envio (Evolution/Baileys)."""
    parts = [str(exc)]
    if getattr(exc, 'response', None):
        parts.append(str(exc.response))
    combined = ' '.join(parts).lower()
    if 'connection closed' in combined or 'precondition required' in combined:
        return (
            'WhatsApp Web desconectou. Abra Configurações → WhatsApp, '
            'verifique o status e escaneie o QR Code novamente.'
        )
    if getattr(exc, 'status_code', None) in (400, 428) and (
        'bad request' in combined or not str(exc).strip()
    ):
        return (
            'Não foi possível enviar pelo WhatsApp Web. '
            'Verifique se a conexão está ativa em Configurações → WhatsApp e tente novamente.'
        )
    return str(exc)


def _normalize_evolution_state(raw_state):
    state = (raw_state or '').strip().lower()
    if state in ('open', 'connected'):
        return 'connected'
    if state in ('connecting', 'pairing', 'qrcode'):
        return 'qr_pending'
    if state in ('close', 'closed', 'disconnected', 'logout'):
        return 'disconnected'
    return 'disconnected'


def _extract_qr_base64(data):
    if not isinstance(data, dict):
        return None
    for key in ('base64', 'qrcode', 'code'):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            raw = val.strip()
            if key == 'code' and not raw.startswith('data:image') and len(raw) < 40:
                continue
            return raw
    for container_key in ('qrcode', 'instance', 'response', 'data'):
        container = data.get(container_key)
        if isinstance(container, dict):
            found = _extract_qr_base64(container)
            if found:
                return found
    return None


def _extract_pairing_code(data):
    if not isinstance(data, dict):
        return None
    for key in ('pairingCode', 'pairing_code'):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    for container_key in ('qrcode', 'instance', 'response', 'data'):
        container = data.get(container_key)
        if isinstance(container, dict):
            found = _extract_pairing_code(container)
            if found:
                return found
    return None


def _extract_phone(data):
    if not isinstance(data, dict):
        return ''
    for key in ('ownerJid', 'wuid', 'phone', 'number'):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return _digits_from_jid(val)
    instance = data.get('instance')
    if isinstance(instance, dict):
        for key in ('ownerJid', 'wuid', 'phone', 'number'):
            val = instance.get(key)
            if isinstance(val, str) and val.strip():
                return _digits_from_jid(val)
    return ''


def _digits_from_jid(value):
    digits = re.sub(r'\D', '', value.split('@')[0])
    return digits[:32]


def fetch_instances():
    data = _request('GET', '/instance/fetchInstances')
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get('instances') or data.get('data')
        if isinstance(items, list):
            return items
    return []


def instance_exists(instance_name):
    name = (instance_name or '').strip()
    if not name:
        return False
    for item in fetch_instances():
        if not isinstance(item, dict):
            continue
        inst = item.get('instance') if isinstance(item.get('instance'), dict) else item
        if (inst.get('instanceName') or inst.get('name') or '').strip() == name:
            return True
    return False


def create_instance(instance_name):
    body = {
        'instanceName': instance_name,
        'integration': 'WHATSAPP-BAILEYS',
        'qrcode': True,
    }
    return _request('POST', '/instance/create', json_body=body)


def _has_qr_payload(data):
    return bool(_extract_qr_base64(data) or _extract_pairing_code(data))


def _is_qr_not_ready(data):
    """Evolution responde {count: N} enquanto Baileys ainda inicia."""
    if not isinstance(data, dict):
        return False
    keys = set(data.keys())
    return keys <= {'count'} or (len(keys) == 1 and 'count' in keys)


def connect_instance(instance_name):
    return _request('GET', f'/instance/connect/{instance_name}')


def recreate_instance(instance_name):
    """Remove instância travada e cria nova sessão com QR."""
    delete_instance(instance_name)
    time.sleep(1.5)
    return create_instance(instance_name)


def wait_for_qr(instance_name, attempts=6, delay=4.0):
    """
    Aguarda QR da Evolution. Uma chamada connect por ciclo (evita loop Baileys).
    """
    last_data = {}
    time.sleep(4)
    for attempt in range(attempts):
        last_data = connect_instance(instance_name)
        if _has_qr_payload(last_data):
            return last_data
        if _is_qr_not_ready(last_data):
            logger.info(
                'Evolution %s: aguardando QR (%s/%s)',
                instance_name, attempt + 1, attempts,
            )
            if attempt < attempts - 1:
                time.sleep(delay)
            continue
        break
    return last_data


def get_connection_state(instance_name):
    data = _request('GET', f'/instance/connectionState/{instance_name}')
    instance = data.get('instance') if isinstance(data.get('instance'), dict) else data
    state_raw = instance.get('state') or instance.get('status') or data.get('state')
    return {
        'state': _normalize_evolution_state(state_raw),
        'raw_state': state_raw,
        'phone': _extract_phone(instance) or _extract_phone(data),
        'data': data,
    }


def logout_instance(instance_name):
    try:
        return _request('DELETE', f'/instance/logout/{instance_name}')
    except EvolutionAPIError as exc:
        if exc.status_code == 404:
            return {}
        raise


def delete_instance(instance_name):
    try:
        return _request('DELETE', f'/instance/delete/{instance_name}')
    except EvolutionAPIError as exc:
        if exc.status_code == 404:
            return {}
        raise


def send_text(instance_name, number, text):
    resolved = resolve_recipient_number(instance_name, number)
    msg = str(text)[:4096]
    body = {
        'number': resolved,
        'text': msg,
        # Mensagens com link (confirmação, termo, assinatura) falham entrega se o
        # preview tenta scrapear URL e quebra o ack Baileys (Evolution 2.3.x).
        'linkPreview': False,
    }
    return _request('POST', f'/message/sendText/{instance_name}', json_body=body)


def send_document(instance_name, number, document_url, filename, caption=None):
    resolved = resolve_recipient_number(instance_name, number)
    body = {
        'number': resolved,
        'mediatype': 'document',
        'media': document_url,
        'fileName': filename or 'documento.pdf',
    }
    if caption:
        body['caption'] = str(caption)[:1024]
    return _request('POST', f'/message/sendMedia/{instance_name}', json_body=body)


def send_buttons(instance_name, number, *, title, description, footer, buttons):
    """
    Botões interativos (reply). buttons: list of {id, displayText}.
    """
    resolved = resolve_recipient_number(instance_name, number)
    body = {
        'number': resolved,
        'title': str(title)[:60],
        'description': str(description)[:1024],
        'footer': str(footer)[:60],
        'buttons': [
            {
                'title': 'reply',
                'displayText': str(b.get('displayText', ''))[:25],
                'id': str(b.get('id', ''))[:128],
            }
            for b in (buttons or [])[:3]
        ],
    }
    return _request('POST', f'/message/sendButtons/{instance_name}', json_body=body)


def send_url_button(instance_name, number, *, title, body_text, button_label, url, footer=''):
    """
    Mensagem com botão de URL (abre link ao tocar).
    Usa sendButtons com tipo 'url' — disponível na Evolution API v2+.
    Fallback automático: se o provider não suportar, lança EvolutionAPIError
    e o chamador deve cair em send_text.

    button_label: texto exibido no botão (ex.: '📝 Ler e Assinar')
    url: URL completa que abre ao tocar o botão
    """
    resolved = resolve_recipient_number(instance_name, number)
    body = {
        'number': resolved,
        'title': str(title)[:60],
        'description': str(body_text)[:1024],
        'footer': str(footer)[:60] if footer else '',
        'buttons': [
            {
                'title': 'url',
                'displayText': str(button_label)[:25],
                'url': str(url),
            }
        ],
    }
    return _request('POST', f'/message/sendButtons/{instance_name}', json_body=body)


def evolution_webhook_url():
    """
    URL pública do webhook LWK na API (não no frontend Vercel).
    SITE_URL em produção costuma ser https://lwksistemas.com.br — não usar para webhook.
    """
    from django.conf import settings

    explicit = (getattr(settings, 'EVOLUTION_WEBHOOK_URL', None) or '').strip()
    if explicit:
        return explicit if explicit.endswith('/') else f'{explicit}/'

    base = (
        getattr(settings, 'API_BASE_URL', None)
        or getattr(settings, 'BACKEND_URL', None)
        or ''
    ).strip().rstrip('/')

    if not base:
        from core.public_urls import get_public_api_base_url

        base = get_public_api_base_url()

    return f'{base}/api/whatsapp/evolution/webhook/'


def set_instance_webhook(instance_name):
    body = {
        'webhook': {
            'enabled': True,
            'url': evolution_webhook_url(),
            'webhookByEvents': False,
            'webhookBase64': False,
            'events': ['MESSAGES_UPSERT', 'CONNECTION_UPDATE'],
        }
    }
    return _request('POST', f'/webhook/set/{instance_name}', json_body=body)
