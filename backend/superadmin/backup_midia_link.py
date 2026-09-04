"""Link assinado para o cliente baixar fotos no Magalu (sem ZIP no servidor)."""
from __future__ import annotations

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, dumps, loads

from core.assinatura_service import normalizar_token_url

TOKEN_SALT = "backup-midia-loja"
TOKEN_MAX_AGE = 21 * 24 * 3600


def gerar_token_backup_midia(*, loja_id: int, slug: str = "") -> str:
    return dumps({"loja_id": int(loja_id), "slug": slug or ""}, salt=TOKEN_SALT)


def decodificar_token_backup_midia(token: str) -> dict | None:
    raw = normalizar_token_url(token)
    if not raw:
        return None
    try:
        payload = loads(raw, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None
    loja_id = payload.get("loja_id")
    if not loja_id:
        return None
    return {"loja_id": int(loja_id), "slug": payload.get("slug") or ""}


def url_pagina_backup_midia(loja) -> str:
    token = gerar_token_backup_midia(loja_id=loja.id, slug=getattr(loja, "slug", "") or "")
    base = (
        getattr(settings, "FRONTEND_URL", None)
        or getattr(settings, "SITE_URL", None)
        or "https://lwksistemas.com.br"
    ).rstrip("/")
    return f"{base}/backup-midia/{token}"
