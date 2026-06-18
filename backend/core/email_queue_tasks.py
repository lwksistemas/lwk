"""Tarefas django-q para envio de e-mail (worker lwks-worker)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_send_email(payload: dict, fail_silently: bool = False) -> int:
    from core.email_delivery import deliver_email_sync
    from core.email_serialize import deserialize_email_message
    from core.email_sync_context import email_sync_only

    token = email_sync_only.set(True)
    try:
        msg = deserialize_email_message(payload)
        return deliver_email_sync(msg, fail_silently=fail_silently)
    except Exception:
        logger.exception(
            'Fila e-mail: falha assunto=%s dest=%s',
            payload.get('subject'),
            payload.get('to'),
        )
        if fail_silently:
            return 0
        raise
    finally:
        email_sync_only.reset(token)
