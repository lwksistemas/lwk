"""
Envio de e-mails transacionais com remetente e Reply-To padronizados.

Produção (Railway): API Resend quando RESEND_API_KEY estiver definida.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Sequence, Union

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

from core.resend_api import resend_api_key, send_via_resend_api

logger = logging.getLogger(__name__)

Recipient = Union[str, Sequence[str]]


def get_from_email() -> str:
    return getattr(
        settings,
        'DEFAULT_FROM_EMAIL',
        'LWK Sistemas <noreply@lwksistemas.com.br>',
    )


def get_reply_to() -> List[str]:
    raw = getattr(settings, 'DEFAULT_REPLY_TO', '') or ''
    if isinstance(raw, (list, tuple)):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        return [e.strip() for e in raw.replace(';', ',').split(',') if e.strip()]
    return []


def prepare_outbound_email(msg: EmailMessage) -> EmailMessage:
    """Aplica remetente e Reply-To em mensagens já montadas (anexos, HTML, etc.)."""
    if not msg.from_email:
        msg.from_email = get_from_email()
    reply = get_reply_to()
    if reply and not msg.reply_to:
        msg.reply_to = reply
    return msg


def _normalize_recipients(recipient_list: Recipient) -> List[str]:
    if isinstance(recipient_list, str):
        return [recipient_list]
    return list(recipient_list)


def create_email_message(
    subject: str,
    body: str,
    to: Recipient,
    *,
    from_email: Optional[str] = None,
    cc: Optional[Recipient] = None,
    bcc: Optional[Recipient] = None,
    **kwargs,
) -> EmailMessage:
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email or get_from_email(),
        to=_normalize_recipients(to),
        cc=_normalize_recipients(cc) if cc else None,
        bcc=_normalize_recipients(bcc) if bcc else None,
        **kwargs,
    )
    return prepare_outbound_email(msg)


def create_email_multipart(
    subject: str,
    body: str,
    to: Recipient,
    *,
    html: Optional[str] = None,
    from_email: Optional[str] = None,
    **kwargs,
) -> EmailMultiAlternatives:
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=from_email or get_from_email(),
        to=_normalize_recipients(to),
        **kwargs,
    )
    if html:
        msg.attach_alternative(html, 'text/html')
    return prepare_outbound_email(msg)


def send_system_mail(
    subject: str,
    message: str,
    recipient_list: Recipient,
    *,
    html_message: Optional[str] = None,
    from_email: Optional[str] = None,
    fail_silently: bool = False,
) -> int:
    """Envia e-mail texto ou texto+HTML com cabeçalhos padronizados."""
    to = _normalize_recipients(recipient_list)
    if html_message:
        msg = create_email_multipart(
            subject,
            message,
            to,
            html=html_message,
            from_email=from_email,
        )
    else:
        msg = create_email_message(
            subject,
            message,
            to,
            from_email=from_email,
        )
    try:
        return msg.send(fail_silently=fail_silently)
    except Exception:
        logger.exception('Falha ao enviar e-mail: assunto=%s destinatarios=%s', subject, to)
        raise


def send_prepared(msg: EmailMessage, *, fail_silently: bool = False) -> int:
    msg = prepare_outbound_email(msg)
    key = resend_api_key()
    if key:
        try:
            send_via_resend_api(msg, api_key=key)
            return 1
        except Exception:
            logger.exception(
                'Falha Resend API: assunto=%s dest=%s',
                msg.subject,
                msg.to,
            )
            if fail_silently:
                return 0
            raise

    if os.environ.get('RAILWAY_ENVIRONMENT'):
        raise RuntimeError(
            'RESEND_API_KEY não está configurada no Railway. '
            'Adicione a chave do Resend e remova EMAIL_HOST / EMAIL_HOST_PASSWORD do Gmail.'
        )

    return msg.send(fail_silently=fail_silently)


# Compatibilidade: send_mail legado com Reply-To
def send_mail_with_reply(
    subject: str,
    message: str,
    recipient_list: Recipient,
    fail_silently: bool = False,
    **kwargs,
) -> int:
    return send_system_mail(
        subject,
        message,
        recipient_list,
        fail_silently=fail_silently,
        from_email=kwargs.get('from_email'),
        html_message=kwargs.get('html_message'),
    )
