"""Evita re-enfileirar quando o envio já roda dentro do worker django-q."""
from __future__ import annotations

import contextvars

email_sync_only: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'email_sync_only',
    default=False,
)
