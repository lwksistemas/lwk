"""Valida URLs de fotos no servidor de mídia da loja."""
from __future__ import annotations

from urllib.parse import urlparse

from core.media_storage import _cpf_cnpj_digits, is_media_url, parse_media_url

from .exceptions import FotoUrlInvalida

# Pastas permitidas para fotos de acompanhamento do paciente.
FOLDERS_FOTO_PACIENTE = frozenset({"fotos"})

# Hosts legados que não podem mais ser usados para fotos de paciente.
HOSTS_BLOQUEADOS = frozenset({
    "cloudinary.com",
    "res.cloudinary.com",
    "cloudinary",
})


def validar_foto_loja(loja, foto_url: str, public_id: str = "") -> None:
    """Garante host exato do media server + path /files/{cnpj}/fotos/..."""
    del public_id  # mantido por compatibilidade da assinatura
    url = (foto_url or "").strip()
    if not url.startswith("https://"):
        raise FotoUrlInvalida("URL da imagem inválida.")

    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        raise FotoUrlInvalida("URL da imagem inválida.")
    if parsed_url.username or parsed_url.password:
        raise FotoUrlInvalida("URL da imagem inválida.")

    hostname = parsed_url.hostname.lower()
    if any(bloqueado in hostname for bloqueado in HOSTS_BLOQUEADOS):
        raise FotoUrlInvalida("URLs de serviços externos de mídia não são permitidas.")

    if not is_media_url(url):
        raise FotoUrlInvalida("Imagem deve estar no servidor de mídia desta clínica.")

    parsed = parse_media_url(url)
    if not parsed:
        raise FotoUrlInvalida("URL de mídia inválida.")

    tenant, folder, filename = parsed
    cnpj = _cpf_cnpj_digits(loja)
    if not cnpj or tenant != cnpj:
        raise FotoUrlInvalida("Imagem fora da pasta autorizada desta clínica.")
    if folder not in FOLDERS_FOTO_PACIENTE:
        raise FotoUrlInvalida("Pasta de mídia não autorizada para fotos de paciente.")
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise FotoUrlInvalida("Nome de arquivo inválido.")
