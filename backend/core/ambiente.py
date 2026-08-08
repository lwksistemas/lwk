"""Segmento de ambiente (beta / producao) — usado em tokens QR e paths."""
from __future__ import annotations

import os
from urllib.parse import urlparse

from django.conf import settings


def ambiente_segment() -> str:
    """Beta (homologação) ou producao."""
    explicit = (os.environ.get("LWK_ENV") or os.environ.get("LWK_AMBIENTE") or "").strip().lower()
    if explicit in ("beta", "staging", "homologacao", "homologação"):
        return "beta"
    if explicit in ("producao", "production", "prod"):
        return "producao"
    frontend = (getattr(settings, "FRONTEND_URL", None) or "").lower()
    if "beta.lwksistemas.com.br" in frontend:
        return "beta"
    return "producao"


def resolve_ambiente_segment(origin_or_base: str | None = None) -> str:
    """beta/producao — prioriza hostname (ex.: beta.lwksistemas.com.br no QR)."""
    if origin_or_base:
        raw = origin_or_base.strip()
        if raw and "://" not in raw:
            raw = f'https://{raw.lstrip("/")}'
        host = (urlparse(raw).hostname or "").lower()
        if host == "beta.lwksistemas.com.br":
            return "beta"
        if host in ("lwksistemas.com.br", "www.lwksistemas.com.br"):
            return "producao"
    return ambiente_segment()
