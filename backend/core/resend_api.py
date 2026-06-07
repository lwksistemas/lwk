"""Envio de e-mail via API HTTP Resend (compartilhado por backend Django e email_delivery)."""
from __future__ import annotations

import base64
import logging
from email.mime.base import MIMEBase

import requests
from django.conf import settings
from django.core.mail.message import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)

RESEND_API_URL = 'https://api.resend.com/emails'


def resend_api_key() -> str:
    return (getattr(settings, 'RESEND_API_KEY', '') or '').strip()


def build_resend_payload(message: EmailMessage) -> dict:
    from_email = message.from_email or getattr(
        settings,
        'DEFAULT_FROM_EMAIL',
        'LWK Sistemas <noreply@lwksistemas.com.br>',
    )

    payload: dict = {
        'from': from_email,
        'to': list(message.to or []),
        'subject': message.subject or '',
    }

    if message.cc:
        payload['cc'] = list(message.cc)
    if message.bcc:
        payload['bcc'] = list(message.bcc)

    reply_to = list(message.reply_to or [])
    if not reply_to:
        raw = getattr(settings, 'DEFAULT_REPLY_TO', '') or ''
        if isinstance(raw, str) and raw.strip():
            reply_to = [e.strip() for e in raw.replace(';', ',').split(',') if e.strip()]
        elif isinstance(raw, (list, tuple)):
            reply_to = [str(x).strip() for x in raw if str(x).strip()]
    if reply_to:
        payload['reply_to'] = reply_to

    html_body = None
    if isinstance(message, EmailMultiAlternatives):
        for content, mimetype in message.alternatives:
            if mimetype == 'text/html':
                html_body = content
                break

    if html_body:
        payload['html'] = html_body
        payload['text'] = message.body or ''
    elif getattr(message, 'content_subtype', 'plain') == 'html':
        payload['html'] = message.body or ''
    else:
        payload['text'] = message.body or ''

    attachments = _build_attachments(message)
    if attachments:
        payload['attachments'] = attachments

    return payload


def _build_attachments(message: EmailMessage) -> list[dict]:
    out: list[dict] = []
    for attachment in message.attachments or []:
        if isinstance(attachment, MIMEBase):
            filename = attachment.get_filename() or 'anexo'
            payload = attachment.get_payload(decode=True) or b''
        elif isinstance(attachment, (tuple, list)) and len(attachment) >= 2:
            filename = attachment[0] or 'anexo'
            content = attachment[1]
            payload = content if isinstance(content, bytes) else str(content).encode('utf-8')
        else:
            continue
        out.append({
            'filename': filename,
            'content': base64.b64encode(payload).decode('ascii'),
        })
    return out


def send_via_resend_api(message: EmailMessage, *, api_key: str | None = None) -> None:
    key = (api_key or resend_api_key()).strip()
    if not key:
        raise ValueError(
            'RESEND_API_KEY não configurada no servidor. '
            'Configure no Railway e remova EMAIL_HOST/EMAIL_HOST_PASSWORD do Gmail.'
        )

    payload = build_resend_payload(message)
    response = requests.post(
        RESEND_API_URL,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        detail = response.text[:500]
        logger.error('Resend API %s: %s', response.status_code, detail)
        raise requests.HTTPError(
            f'Resend API {response.status_code}: {detail}',
            response=response,
        )
