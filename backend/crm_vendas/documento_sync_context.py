"""Evita re-enfileirar envio de documento quando já roda no worker django-q."""
from __future__ import annotations

import contextvars

documento_envio_sync_only: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'documento_envio_sync_only',
    default=False,
)
