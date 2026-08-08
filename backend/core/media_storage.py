"""Serviço de armazenamento de mídia (media.lwksistemas.com.br).

Faz upload/download no servidor media.lwksistemas.com.br.
Estrutura:
  /storage/{cpf_cnpj}/fotos|docs|...     — cada cliente
  /storage/superadmin/...                — assets do superadmin (sem loja)
  /storage/suporte/...                   — assets do suporte (sem loja)

Uso:
    from core.media_storage import media_upload, media_url

    url = media_upload(loja, file_bytes, filename="foto.jpg", folder="fotos")
    # Retorna: https://media.lwksistemas.com.br/files/41449198000172/fotos/abc123.jpg
"""
import logging
import os
import re
from io import BytesIO
from typing import BinaryIO

import requests

logger = logging.getLogger(__name__)

MEDIA_SERVER_URL = os.environ.get(
    "MEDIA_SERVER_URL", "https://media.lwksistemas.com.br"
)
MEDIA_API_TOKEN = os.environ.get(
    "MEDIA_API_TOKEN",
    os.environ.get("SECRET_KEY", ""),
)

MEDIA_TENANT_SUPERADMIN = "superadmin"
MEDIA_TENANT_SUPORTE = "suporte"
MEDIA_SYSTEM_TENANTS = frozenset({MEDIA_TENANT_SUPERADMIN, MEDIA_TENANT_SUPORTE})

# Compat: imports antigos
MEDIA_SYSTEM_CNPJ = MEDIA_TENANT_SUPERADMIN

_FILES_PATH_RE = re.compile(
    r"/files/(?P<tenant>\d{11}|\d{14}|superadmin|suporte)/(?P<folder>[\w-]+)/(?P<filename>[^/?#]+)$"
)


def normalize_media_tenant(value: str | None) -> str | None:
    """Normaliza e valida a chave de tenant do servidor de mídia."""
    raw = (value or "").strip()
    if not raw:
        return None
    if raw in MEDIA_SYSTEM_TENANTS:
        return raw
    digits = re.sub(r"\D", "", raw)
    if len(digits) in (11, 14):
        return digits
    return None


def _cpf_cnpj_digits(loja) -> str:
    """Extrai CPF/CNPJ só dígitos da loja (ou tenant de sistema se marcado)."""
    # Objetos SimpleNamespace de sistema podem trazer tenant_key direto
    tenant_key = getattr(loja, "media_tenant", None) or getattr(loja, "slug", None)
    if tenant_key in MEDIA_SYSTEM_TENANTS:
        return tenant_key

    cpf_cnpj = getattr(loja, "cpf_cnpj", None) or ""
    digits = re.sub(r"\D", "", cpf_cnpj)
    if len(digits) in (11, 14):
        return digits
    # Fallback: slug
    slug = getattr(loja, "slug", None) or ""
    if slug in MEDIA_SYSTEM_TENANTS:
        return slug
    slug_digits = re.sub(r"\D", "", slug)
    if len(slug_digits) in (11, 14):
        return slug_digits
    return digits or str(getattr(loja, "id", "unknown"))


def media_upload_tenant(
    tenant: str,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Faz upload para um tenant (CPF/CNPJ, superadmin ou suporte)."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        logger.error("media_upload_tenant: tenant inválido %r", tenant)
        return None

    url = f"{MEDIA_SERVER_URL}/upload/{tenant_key}/"
    headers = {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}

    if isinstance(file_data, bytes):
        file_obj = BytesIO(file_data)
    else:
        file_obj = file_data

    try:
        response = requests.post(
            url,
            headers=headers,
            files={"file": (filename, file_obj)},
            data={"folder": folder},
            timeout=60,
        )

        if response.status_code == 201:
            data = response.json()
            file_url = f"{MEDIA_SERVER_URL}{data['url']}"
            logger.info("media_upload OK: %s (%d bytes)", file_url, data.get("size", 0))
            return file_url

        logger.error(
            "media_upload falhou: HTTP %s — %s",
            response.status_code,
            response.text[:200],
        )
        return None
    except Exception as exc:
        logger.exception("media_upload erro: %s", exc)
        return None


def media_upload_cnpj(
    cnpj: str,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Compat: alias de media_upload_tenant."""
    return media_upload_tenant(cnpj, file_data, filename=filename, folder=folder)


def media_upload(
    loja,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Faz upload de arquivo para o servidor de mídia.

    Args:
        loja: objeto Loja (com cpf_cnpj) ou namespace com media_tenant/slug de sistema
        file_data: bytes ou file-like object
        filename: nome original do arquivo
        folder: subpasta (fotos, docs, avatars, recibos, contratos)

    Returns:
        URL pública do arquivo ou None em caso de erro.
    """
    tenant = _cpf_cnpj_digits(loja)
    if not normalize_media_tenant(tenant):
        logger.error("media_upload: loja sem CPF/CNPJ válido (%r)", tenant)
        return None
    return media_upload_tenant(tenant, file_data, filename=filename, folder=folder)


def media_upload_from_url(
    loja,
    source_url: str,
    *,
    folder: str = "fotos",
) -> str | None:
    """Baixa arquivo de uma URL e faz upload para o servidor de mídia."""
    try:
        resp = requests.get(source_url, timeout=30)
        if resp.status_code != 200:
            logger.warning("media_upload_from_url: falha ao baixar %s", source_url)
            return None

        from pathlib import PurePosixPath
        path = PurePosixPath(source_url.split("?")[0])
        filename = path.name or "image.jpg"

        return media_upload(loja, resp.content, filename=filename, folder=folder)
    except Exception as exc:
        logger.exception("media_upload_from_url erro: %s", exc)
        return None


def media_delete(loja, filename: str, folder: str = "fotos") -> bool:
    """Deleta arquivo do servidor de mídia."""
    tenant = _cpf_cnpj_digits(loja)
    return media_delete_tenant(tenant, filename, folder=folder)


def media_delete_tenant(tenant: str, filename: str, folder: str = "fotos") -> bool:
    """Deleta arquivo de um tenant específico."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return False
    url = f"{MEDIA_SERVER_URL}/upload/{tenant_key}/{folder}/{filename}"
    headers = {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}

    try:
        response = requests.delete(url, headers=headers, timeout=15)
        return response.status_code == 200
    except Exception as exc:
        logger.warning("media_delete erro: %s", exc)
        return False


def media_url(loja, filename: str, folder: str = "fotos") -> str:
    """Constrói URL pública de um arquivo."""
    tenant = _cpf_cnpj_digits(loja)
    return f"{MEDIA_SERVER_URL}/files/{tenant}/{folder}/{filename}"


def is_media_url(url: str) -> bool:
    """Verifica se a URL é do servidor de mídia local."""
    return "media.lwksistemas.com.br" in (url or "")


def parse_media_url(url: str) -> tuple[str, str, str] | None:
    """Extrai (tenant, folder, filename) de uma URL pública de mídia."""
    if not is_media_url(url):
        return None
    match = _FILES_PATH_RE.search(url or "")
    if not match:
        return None
    return match.group("tenant"), match.group("folder"), match.group("filename")


def media_delete_by_url(url: str) -> bool:
    """Remove arquivo a partir da URL pública completa no servidor de mídia."""
    parsed = parse_media_url(url)
    if not parsed:
        logger.warning("media_delete_by_url: path não reconhecido: %s", url)
        return False
    tenant, folder, filename = parsed
    return media_delete_tenant(tenant, filename, folder=folder)
