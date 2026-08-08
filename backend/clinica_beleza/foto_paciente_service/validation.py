"""Valida URLs de fotos no servidor de mídia da loja."""
from __future__ import annotations

import re

from core.media_storage import MEDIA_SERVER_URL, _cpf_cnpj_digits, is_media_url

from .exceptions import FotoUrlInvalida


def validar_foto_loja(loja, foto_url: str, public_id: str = "") -> None:
    """Garante que a URL é do servidor de mídia na pasta da loja."""
    del public_id  # mantido por compatibilidade da assinatura
    url = (foto_url or "").strip()
    if not url.startswith("https://"):
        raise FotoUrlInvalida("URL da imagem inválida.")
    if not is_media_url(url):
        raise FotoUrlInvalida("Imagem deve estar no servidor de mídia desta clínica.")

    cnpj = _cpf_cnpj_digits(loja)
    if not cnpj:
        raise FotoUrlInvalida("Configuração de upload indisponível.")
    base = (MEDIA_SERVER_URL or "https://media.lwksistemas.com.br").rstrip("/")
    expected = f"{base}/files/{cnpj}/"
    if not url.lower().startswith(expected.lower()):
        if not re.search(rf"/files/{re.escape(cnpj)}/", url, re.IGNORECASE):
            raise FotoUrlInvalida("Imagem fora da pasta autorizada desta clínica.")
