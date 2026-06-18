"""Evita re-enfileirar webhook Asaas quando já roda dentro do worker django-q."""
from __future__ import annotations

import contextvars

asaas_webhook_sync_only: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'asaas_webhook_sync_only',
    default=False,
)
