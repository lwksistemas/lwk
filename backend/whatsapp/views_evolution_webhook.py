"""
Webhook Evolution API — respostas de confirmação de agendamento via WhatsApp.
"""
import json
import logging
import re

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def _loja_id_from_instance(instance_name: str) -> int | None:
    m = re.match(r'^lwk_loja_(\d+)$', (instance_name or '').strip())
    return int(m.group(1)) if m else None


def _extract_phone_from_jid(jid: str) -> str:
    return re.sub(r'\D', '', (jid or '').split('@')[0])


def _normalize_reply_text(texto: str) -> str:
    t = re.sub(r'[^\w\sáàâãéèêíìîóòôõúùûç]', '', (texto or '').strip().lower())
    return re.sub(r'\s+', ' ', t).strip()


def _extract_button_id(message: dict) -> str:
    if not isinstance(message, dict):
        return ''
    for key in ('buttonsResponseMessage', 'templateButtonReplyMessage'):
        block = message.get(key)
        if isinstance(block, dict):
            for field in ('selectedButtonId', 'selectedId', 'buttonId'):
                val = block.get(field)
                if isinstance(val, str) and val.strip():
                    return val.strip()
    interactive = message.get('interactiveResponseMessage')
    if isinstance(interactive, dict):
        native = interactive.get('nativeFlowResponseMessage')
        if isinstance(native, dict):
            for field in ('name', 'paramsJson'):
                val = native.get(field)
                if isinstance(val, str) and val.strip():
                    return val.strip()
    return ''


def _extract_message_text(message: dict) -> str:
    if not isinstance(message, dict):
        return ''
    if isinstance(message.get('conversation'), str):
        return message['conversation']
    ext = message.get('extendedTextMessage')
    if isinstance(ext, dict) and isinstance(ext.get('text'), str):
        return ext['text']
    btn = message.get('buttonsResponseMessage')
    if isinstance(btn, dict):
        for field in ('selectedDisplayText', 'selectedButtonId', 'selectedId'):
            val = btn.get(field)
            if isinstance(val, str) and val.strip():
                return val.strip()
    tmpl = message.get('templateButtonReplyMessage')
    if isinstance(tmpl, dict):
        for field in ('selectedDisplayText', 'selectedId'):
            val = tmpl.get(field)
            if isinstance(val, str) and val.strip():
                return val.strip()
    list_resp = message.get('listResponseMessage')
    if isinstance(list_resp, dict) and isinstance(list_resp.get('singleSelectReply'), dict):
        sel = list_resp['singleSelectReply']
        for field in ('selectedRowId', 'title'):
            val = sel.get(field)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ''


def _message_dict_from_data(data: dict) -> dict:
    """Extrai o dict message de payloads Evolution (formatos variados)."""
    if not isinstance(data, dict):
        return {}
    msg = data.get('message')
    if isinstance(msg, dict):
        return msg
    # Alguns payloads trazem o tipo no root
    for key in (
        'buttonsResponseMessage',
        'templateButtonReplyMessage',
        'listResponseMessage',
        'conversation',
        'extendedTextMessage',
    ):
        if key in data:
            return data
    return {}


def _parse_webhook_payload(body) -> list[dict]:
    """Normaliza payload Evolution em lista de eventos."""
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    if not isinstance(body, dict):
        return []

    data = body.get('data')
    if isinstance(data, dict) and (_message_dict_from_data(data) or data.get('key')):
        return [body]

    if body.get('message') or body.get('key'):
        return [{
            'event': 'messages.upsert',
            'instance': body.get('instance'),
            'data': body,
        }]

    event_name = (body.get('event') or '').lower().replace('_', '.')
    if event_name == 'messages.upsert':
        return [body]

    if isinstance(data, list):
        return [
            {'event': 'messages.upsert', 'instance': body.get('instance'), 'data': item}
            for item in data if isinstance(item, dict)
        ]

    return []


@method_decorator(csrf_exempt, name='dispatch')
class EvolutionWebhookView(View):
    """POST /api/whatsapp/evolution/webhook/"""

    def post(self, request):
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponse('OK', status=200)

        events = _parse_webhook_payload(body)
        if not events:
            logger.debug('Evolution webhook: payload sem eventos reconhecidos: %s', list(body.keys()) if isinstance(body, dict) else type(body))

        for event in events:
            self._handle_event(event)

        return HttpResponse('OK', status=200)

    def get(self, request):
        return JsonResponse({'status': 'ok', 'service': 'evolution-webhook'})

    def _handle_event(self, event: dict):
        event_name = (event.get('event') or 'messages.upsert').lower().replace('_', '.')
        if event_name not in ('messages.upsert', ''):
            return

        instance = (event.get('instance') or '').strip()
        loja_id = _loja_id_from_instance(instance)
        if not loja_id:
            logger.debug('Evolution webhook: instance desconhecida %s', instance)
            return

        data = event.get('data')
        if not isinstance(data, dict):
            return

        key = data.get('key') if isinstance(data.get('key'), dict) else {}
        if key.get('fromMe') is True:
            return

        remote_jid = key.get('remoteJid') or data.get('remoteJid') or ''
        # Ignorar grupos (@g.us) — promoções e mensagens de terceiros não são confirmações 1:1
        if remote_jid.endswith('@g.us'):
            return
        telefone = _extract_phone_from_jid(remote_jid)
        if not telefone:
            sender = event.get('sender') or data.get('sender') or ''
            telefone = _extract_phone_from_jid(str(sender))
        if not telefone:
            return

        message = _message_dict_from_data(data)
        button_id = _extract_button_id(message)
        texto = _extract_message_text(message)

        # messageType no root (Evolution v2)
        if not button_id and not texto:
            msg_type = (data.get('messageType') or '').lower()
            if 'button' in msg_type or 'interactive' in msg_type:
                texto = msg_type

        if not button_id and not texto:
            logger.debug(
                'Evolution webhook loja=%s: mensagem sem texto/botão. keys=%s',
                loja_id, list(message.keys()) if message else list(data.keys()),
            )
            return

        from clinica_beleza.agenda_confirmacao_service import processar_resposta_whatsapp

        try:
            result = processar_resposta_whatsapp(
                loja_id,
                telefone,
                texto=texto,
                button_id=button_id,
            )
        except Exception as exc:
            logger.exception(
                'Evolution webhook loja=%s tel=…%s erro ao processar confirmação: %s',
                loja_id,
                telefone[-4:],
                exc,
            )
            return
        if not result:
            logger.debug(
                'Evolution webhook loja=%s tel=…%s: não é confirmação (texto=%r button=%r)',
                loja_id, telefone[-4:], texto[:40] if texto else '', button_id[:40] if button_id else '',
            )
            return

        logger.info(
            'Evolution webhook loja=%s tel=…%s ok=%s status=%s appt=%s msg=%s',
            loja_id, telefone[-4:], result.ok, result.status, result.appointment_id, result.message[:80],
        )
