from datetime import timedelta
from urllib.parse import quote, urlparse

from django.conf import settings
from django.core.signing import BadSignature, dumps, loads
from django.utils import timezone

from core.cloudinary_folders import resolve_ambiente_segment
from core.mfa_service import qr_code_base64

from .constants import MODULO, PATH_PUBLICO, TOKEN_EXPIRACAO_HORAS


def gerar_token_foto(
    consulta_id: int,
    patient_id: int,
    loja_id: int,
    ambiente: str | None = None,
) -> str:
    amb = ambiente if ambiente in ("beta", "producao") else resolve_ambiente_segment()
    payload = {
        "doc_type": "foto_paciente",
        "consulta_id": consulta_id,
        "patient_id": patient_id,
        "loja_id": loja_id,
        "modulo": MODULO,
        "ambiente": amb,
        "exp": int((timezone.now() + timedelta(hours=TOKEN_EXPIRACAO_HORAS)).timestamp()),
    }
    return dumps(payload)


def decodificar_token_foto(token: str) -> dict | None:
    from core.assinatura_service import normalizar_token_url

    token = normalizar_token_url(token)
    if not token:
        return None
    try:
        payload = loads(token)
    except (BadSignature, Exception):
        return None
    if payload.get("doc_type") != "foto_paciente":
        return None
    exp = payload.get("exp")
    if exp and timezone.now().timestamp() > exp:
        return None
    return payload


def build_link_foto(token: str, frontend_base: str | None = None) -> str:
    base = (frontend_base or getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")).rstrip("/")
    return f"{base}{PATH_PUBLICO}{quote(token, safe='')}"


def frontend_base_permitido(origin: str | None) -> str | None:
    """Aceita só origens LWK (beta/produção/local) para o link do QR."""
    raw = (origin or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = f"https://{raw.lstrip('/')}"
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    host = (parsed.hostname or "").lower()
    if host in (
        "beta.lwksistemas.com.br",
        "lwksistemas.com.br",
        "www.lwksistemas.com.br",
        "localhost",
        "127.0.0.1",
    ) or host.endswith(".lwksistemas.com.br"):
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return None


def resolver_frontend_base_qr(request=None, frontend_origin: str | None = None) -> str | None:
    """Prioriza origem enviada pelo painel (beta vs produção)."""
    if request is not None:
        for candidate in (
            frontend_origin,
            getattr(request, "headers", {}).get("Origin") if hasattr(request, "headers") else None,
        ):
            base = frontend_base_permitido(candidate)
            if base:
                return base
        referer = getattr(request, "META", {}).get("HTTP_REFERER", "")
        if referer:
            ref = urlparse(referer)
            if ref.scheme and ref.netloc:
                base = frontend_base_permitido(f"{ref.scheme}://{ref.netloc}")
                if base:
                    return base
    elif frontend_origin:
        return frontend_base_permitido(frontend_origin)
    return None


def gerar_qr_foto(consulta, frontend_base: str | None = None) -> dict:
    ambiente = resolve_ambiente_segment(frontend_base)
    token = gerar_token_foto(
        consulta.id,
        consulta.patient_id,
        consulta.loja_id,
        ambiente=ambiente,
    )
    url = build_link_foto(token, frontend_base)
    return {
        "token": token,
        "url": url,
        "qr_base64": qr_code_base64(url),
        "expira_em_horas": TOKEN_EXPIRACAO_HORAS,
    }


def ambiente_do_token_foto(payload: dict, request=None) -> str:
    """Ambiente Cloudinary do token QR; fallback pela origem da requisição."""
    amb = payload.get("ambiente")
    if amb in ("beta", "producao"):
        return amb
    base = resolver_frontend_base_qr(request) if request is not None else None
    return resolve_ambiente_segment(base)
