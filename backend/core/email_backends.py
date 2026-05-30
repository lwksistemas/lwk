"""
Backend de e-mail via API Resend (Django EMAIL_BACKEND).
"""
from __future__ import annotations

import logging

from django.core.mail.backends.base import BaseEmailBackend

from core.resend_api import resend_api_key, send_via_resend_api

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Envia e-mails pela API HTTP do Resend."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        if not resend_api_key():
            raise ValueError('RESEND_API_KEY não configurada')

        sent = 0
        for message in email_messages:
            try:
                send_via_resend_api(message)
                sent += 1
            except Exception:
                logger.exception(
                    'Resend: falha ao enviar e-mail assunto=%s dest=%s',
                    message.subject,
                    message.to,
                )
                if not self.fail_silently:
                    raise
        return sent
