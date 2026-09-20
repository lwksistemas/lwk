"""Token opaco para PDF público (WhatsApp / Evolution).

A URL leva o token; o cache guarda só o hash. Quem lê o Redis não monta o link.
TTL 5 minutos. Sem uso único — a Evolution pode baixar o mesmo URL mais de uma vez.
"""
from __future__ import annotations

import hashlib
import secrets

from django.core.cache import cache as django_cache

TTL_PDF_PUBLICO = 300
PREFIX_ORCAMENTO = "orcamento_pdf"
PREFIX_RECIBO = "recibo_pdf"
PREFIX_PEDIDO = "pedido_compra_pdf"
PREFIX_TERMO = "termo_pdf"


def _chave_hash(prefix: str, token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def gravar_pdf_publico(prefix: str, payload: dict, *, ttl: int = TTL_PDF_PUBLICO) -> str:
    """Grava o payload e devolve o token da URL (não o hash)."""
    token = secrets.token_urlsafe(32)
    django_cache.set(_chave_hash(prefix, token), payload, ttl)
    return token


def ler_pdf_publico(prefix: str, token: str) -> dict | None:
    """Lê o payload só pela chave hasheada (o token da URL não fica no Redis)."""
    if not token or len(token) > 200:
        return None
    cached = django_cache.get(_chave_hash(prefix, token))
    return cached if isinstance(cached, dict) else None
