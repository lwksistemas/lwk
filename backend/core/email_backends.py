"""
Backend de e-mail via API Resend (Django EMAIL_BACKEND).
Enfileira envios quando USE_TASK_QUEUE=true no lwks-backend.
"""
from __future__ import annotations

import logging

from django.core.mail.backends.base import BaseEmailBackend

from core.resend_api import resend_api_key

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Envia e-mails pela API HTTP do Resend (direto ou via fila)."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        from core.email_delivery import deliver_email_message
        from core.email_sync_context import email_sync_only

        if email_sync_only.get():
            return self._send_messages_sync(email_messages)

        from core.email_delivery import _should_enqueue_email

        if _should_enqueue_email():
            sent = 0
            for message in email_messages:
                try:
                    sent += deliver_email_message(message, fail_silently=self.fail_silently)
                except Exception:
                    logger.exception(
                        'Resend: falha ao enfileirar e-mail assunto=%s dest=%s',
                        message.subject,
                        message.to,
                    )
                    if not self.fail_silently:
                        raise
            return sent

        return self._send_messages_sync(email_messages)

    def _send_messages_sync(self, email_messages):
        if not resend_api_key():
            raise ValueError('RESEND_API_KEY não configurada')

        from core.email_delivery import deliver_email_sync

        sent = 0
        for message in email_messages:
            try:
                sent += deliver_email_sync(message, fail_silently=self.fail_silently)
            except Exception:
                logger.exception(
                    'Resend: falha ao enviar e-mail assunto=%s dest=%s',
                    message.subject,
                    message.to,
                )
                if not self.fail_silently:
                    raise
        return sent
