"""Token curto para a Evolution baixar o PDF assinado.

A URL leva o token. O cache guarda só o hash. Vale por 15 minutos,
tempo de a Evolution buscar o arquivo mais de uma vez.
"""
from __future__ import annotations

import hashlib
import secrets

from django.core.cache import cache as django_cache

TTL_PDF_ASSINADO = 900
PREFIX_PDF_ASSINADO = "crm_pdf_assinado"


def _chave(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{PREFIX_PDF_ASSINADO}_{digest}"


def gravar_pdf_assinado(pdf_bytes: bytes, filename: str) -> str:
    token = secrets.token_urlsafe(32)
    django_cache.set(_chave(token), {"pdf": pdf_bytes, "filename": filename}, TTL_PDF_ASSINADO)
    return token


def ler_pdf_assinado(token: str) -> dict | None:
    if not token or len(token) > 200:
        return None
    cached = django_cache.get(_chave(token))
    return cached if isinstance(cached, dict) else None
