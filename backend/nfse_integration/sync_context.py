"""Evita re-enfileirar quando a emissão já roda dentro do worker django-q."""
from __future__ import annotations

import contextvars

nfse_sync_only: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "nfse_sync_only",
    default=False,
)
