"""Evita re-enfileirar webhook Mercado Pago quando já roda no worker django-q."""
from __future__ import annotations

import contextvars

mercadopago_webhook_sync_only: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'mercadopago_webhook_sync_only',
    default=False,
)
