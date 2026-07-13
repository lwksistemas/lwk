"""Envio de e-mails transacionais com remetente e Reply-To padronizados.

Produção (Railway): API Resend quando RESEND_API_KEY estiver definida.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Sequence

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

from core.resend_api import resend_api_key, send_via_resend_api

logger = logging.getLogger(__name__)

Recipient = str | Sequence[str]
MAX_EMAIL_QUEUE_BYTES = 4 * 1024 * 1024


def _should_enqueue_email() -> bool:
    from core.email_sync_context import email_sync_only
    from core.task_queue import task_queue_enabled

    return task_queue_enabled() and not email_sync_only.get()


def deliver_email_sync(msg: EmailMessage, *, fail_silently: bool = False) -> int:
    """Envio síncrono (Resend API ou backend Django)."""
    msg = prepare_outbound_email(msg)
    key = resend_api_key()
    if key:
        try:
            send_via_resend_api(msg, api_key=key)
            return 1
        except Exception:
            logger.exception(
                "Falha Resend API: assunto=%s dest=%s",
                msg.subject,
                msg.to,
            )
            if fail_silently:
                return 0
            raise

    if os.environ.get("RAILWAY_ENVIRONMENT"):
        raise RuntimeError(
            "RESEND_API_KEY não está configurada no Railway. "
            "Adicione a chave do Resend e remova EMAIL_HOST / EMAIL_HOST_PASSWORD do Gmail.",
        )

    return msg.send(fail_silently=fail_silently)


def deliver_email_message(msg: EmailMessage, *, fail_silently: bool = False) -> int:
    """Envia e-mail na hora ou enfileira para o lwks-worker."""
    from core.email_serialize import payload_too_large_for_queue, serialize_email_message
    from core.task_queue import enqueue_task

    prepared = prepare_outbound_email(msg)
    if not _should_enqueue_email():
        return deliver_email_sync(prepared, fail_silently=fail_silently)

    payload = serialize_email_message(prepared)
    if payload_too_large_for_queue(payload, MAX_EMAIL_QUEUE_BYTES):
        logger.info(
            "E-mail grande (%s bytes) — envio síncrono: assunto=%s",
            payload.get("payload_bytes"),
            payload.get("subject"),
        )
        return deliver_email_sync(prepared, fail_silently=fail_silently)

    to_label = (payload.get("to") or ["?"])[0]
    task_key = abs(hash((payload.get("subject", ""), to_label, payload.get("payload_bytes", 0))))
    enqueue_task(
        f"email-{task_key}",
        "core.email_queue_tasks.run_send_email",
        payload,
        fail_silently,
    )
    return 1


def get_from_email() -> str:
    return getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        "LWK Sistemas <noreply@lwksistemas.com.br>",
    )


def get_reply_to() -> list[str]:
    raw = getattr(settings, "DEFAULT_REPLY_TO", "") or ""
    if isinstance(raw, (list, tuple)):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        return [e.strip() for e in raw.replace(";", ",").split(",") if e.strip()]
    return []


def prepare_outbound_email(msg: EmailMessage) -> EmailMessage:
    """Aplica remetente e Reply-To em mensagens já montadas (anexos, HTML, etc.)."""
    if not msg.from_email:
        msg.from_email = get_from_email()
    reply = get_reply_to()
    if reply and not msg.reply_to:
        msg.reply_to = reply
    return msg


def _normalize_recipients(recipient_list: Recipient) -> list[str]:
    if isinstance(recipient_list, str):
        return [recipient_list]
    return list(recipient_list)


def create_email_message(
    subject: str,
    body: str,
    to: Recipient,
    *,
    from_email: str | None = None,
    cc: Recipient | None = None,
    bcc: Recipient | None = None,
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
    html: str | None = None,
    from_email: str | None = None,
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
        msg.attach_alternative(html, "text/html")
    return prepare_outbound_email(msg)


def send_system_mail(
    subject: str,
    message: str,
    recipient_list: Recipient,
    *,
    html_message: str | None = None,
    from_email: str | None = None,
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
        return deliver_email_message(msg, fail_silently=fail_silently)
    except Exception:
        logger.exception("Falha ao enviar e-mail: assunto=%s destinatarios=%s", subject, to)
        raise


def send_prepared(msg: EmailMessage, *, fail_silently: bool = False) -> int:
    return deliver_email_message(msg, fail_silently=fail_silently)


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
        from_email=kwargs.get("from_email"),
        html_message=kwargs.get("html_message"),
    )
