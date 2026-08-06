"""Serviço de armazenamento de mídia — substitui Cloudinary.

Faz upload/download no servidor media.lwksistemas.com.br.
Estrutura: /storage/{cpf_cnpj}/{folder}/{filename}

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


def _cpf_cnpj_digits(loja) -> str:
    """Extrai CPF/CNPJ só dígitos da loja."""
    cpf_cnpj = getattr(loja, "cpf_cnpj", None) or ""
    digits = re.sub(r"\D", "", cpf_cnpj)
    if len(digits) in (11, 14):
        return digits
    # Fallback: slug
    slug = getattr(loja, "slug", None) or ""
    slug_digits = re.sub(r"\D", "", slug)
    if len(slug_digits) in (11, 14):
        return slug_digits
    return digits or str(getattr(loja, "id", "unknown"))


def media_upload(
    loja,
    file_data: bytes | BinaryIO,
    *,
    filename: str = "upload.jpg",
    folder: str = "fotos",
) -> str | None:
    """Faz upload de arquivo para o servidor de mídia.

    Args:
        loja: objeto Loja (com cpf_cnpj)
        file_data: bytes ou file-like object
        filename: nome original do arquivo
        folder: subpasta (fotos, docs, avatars, recibos, contratos)

    Returns:
        URL pública do arquivo ou None em caso de erro.
    """
    cnpj = _cpf_cnpj_digits(loja)
    if not cnpj:
        logger.error("media_upload: loja sem CPF/CNPJ")
        return None

    url = f"{MEDIA_SERVER_URL}/upload/{cnpj}/"
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
        else:
            logger.error(
                "media_upload falhou: HTTP %s — %s",
                response.status_code,
                response.text[:200],
            )
            return None
    except Exception as exc:
        logger.exception("media_upload erro: %s", exc)
        return None


def media_upload_from_url(
    loja,
    source_url: str,
    *,
    folder: str = "fotos",
) -> str | None:
    """Baixa imagem de uma URL (ex: Cloudinary) e faz upload para o servidor de mídia."""
    try:
        resp = requests.get(source_url, timeout=30)
        if resp.status_code != 200:
            logger.warning("media_upload_from_url: falha ao baixar %s", source_url)
            return None

        # Extrair extensão da URL
        from pathlib import PurePosixPath
        path = PurePosixPath(source_url.split("?")[0])
        filename = path.name or "image.jpg"

        return media_upload(loja, resp.content, filename=filename, folder=folder)
    except Exception as exc:
        logger.exception("media_upload_from_url erro: %s", exc)
        return None


def media_delete(loja, filename: str, folder: str = "fotos") -> bool:
    """Deleta arquivo do servidor de mídia."""
    cnpj = _cpf_cnpj_digits(loja)
    url = f"{MEDIA_SERVER_URL}/upload/{cnpj}/{folder}/{filename}"
    headers = {"Authorization": f"Bearer {MEDIA_API_TOKEN}"}

    try:
        response = requests.delete(url, headers=headers, timeout=15)
        return response.status_code == 200
    except Exception as exc:
        logger.warning("media_delete erro: %s", exc)
        return False


def media_url(loja, filename: str, folder: str = "fotos") -> str:
    """Constrói URL pública de um arquivo."""
    cnpj = _cpf_cnpj_digits(loja)
    return f"{MEDIA_SERVER_URL}/files/{cnpj}/{folder}/{filename}"


def is_media_url(url: str) -> bool:
    """Verifica se a URL é do servidor de mídia local."""
    return "media.lwksistemas.com.br" in (url or "")


def is_cloudinary_url(url: str) -> bool:
    """Verifica se a URL é do Cloudinary."""
    return "cloudinary.com" in (url or "")
