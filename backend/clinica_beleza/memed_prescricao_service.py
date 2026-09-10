"""Busca e arquiva PDFs de prescrições emitidas na Memed."""
from __future__ import annotations

import ipaddress
import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests

from core.media_storage import folder_media_paciente, is_media_url, media_upload

from .memed_config import memed_config as _memed_config
from .memed_config import memed_credentials as _memed_credentials

logger = logging.getLogger(__name__)

_URL_HTTP = re.compile(r"^https?://", re.IGNORECASE)
_MEMED_HOST = "memed.com.br"


def url_pdf_permitida(url: str) -> bool:
    """True só para HTTPS da Memed (*.memed.com.br) ou do servidor de mídia LWK.

    Impede SSRF: o cliente não pode mandar o backend baixar URL arbitrária.
    """
    raw = (url or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    if host == _MEMED_HOST or host.endswith(f".{_MEMED_HOST}"):
        return True
    return is_media_url(raw)


def _baixar_pdf_url_permitida(url: str) -> bytes | None:
    """Baixa PDF só se a URL passar na allowlist. Sem follow de redirect."""
    if not url_pdf_permitida(url):
        logger.warning("PDF Memed recusado (host não permitido): %s", (url or "")[:120])
        return None
    try:
        resp = requests.get(
            url,
            timeout=45,
            allow_redirects=False,
            headers={"User-Agent": "LWK-Sistemas/1.0"},
        )
    except requests.RequestException as exc:
        logger.debug("Download PDF Memed falhou: %s", exc)
        return None
    if resp.status_code != 200:
        return None
    return _resposta_e_pdf_bruto(resp)


def resolver_prescritor_id_profissional(professional) -> str | None:
    """CPF ou registro+UF do profissional para a API Memed."""
    if not professional:
        return None
    cpf = "".join(ch for ch in (getattr(professional, "cpf", "") or "") if ch.isdigit())
    if len(cpf) == 11:
        return cpf
    raw = (getattr(professional, "registro_profissional", "") or "").strip().upper()
    if not raw:
        return None
    match_uf = re.search(r"[-\s/]*([A-Z]{2})\s*$", raw)
    uf = match_uf.group(1) if match_uf else (getattr(professional, "conselho_uf", "") or "").strip().upper()
    registro = "".join(ch for ch in raw if ch.isalnum())
    if uf and registro.endswith(uf):
        registro = registro[: -len(uf)]
    if registro:
        return f"{registro}{uf}" if uf else registro
    return None


def _obter_token_prescritor(prescritor_id: str) -> str | None:
    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    if not api_key or not secret_key:
        return None
    url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor_id}"
    try:
        resp = requests.get(
            url,
            params={"api-key": api_key, "secret-key": secret_key},
            headers={"Accept": "application/vnd.api+json", "Content-Type": "application/json"},
            timeout=15,
        )
        if not resp.ok:
            logger.warning("Memed token prescritor %s: HTTP %s", prescritor_id, resp.status_code)
            return None
        return ((resp.json() or {}).get("data") or {}).get("attributes", {}).get("token")
    except requests.RequestException as exc:
        logger.warning("Memed token prescritor %s: %s", prescritor_id, exc)
        return None


def _extrair_url_pdf_de_objeto(obj: Any, profundidade: int = 0) -> str:
    if profundidade > 8 or obj is None:
        return ""
    if isinstance(obj, str):
        s = obj.strip()
        if _URL_HTTP.match(s) and (".pdf" in s.lower() or "memed" in s.lower() or "prescri" in s.lower()):
            return s[:500]
        return ""
    if isinstance(obj, dict):
        for chave in (
            "url_pdf", "pdf_url", "link_pdf", "pdf", "url", "link",
            "secure_url", "download_url", "arquivo_url",
        ):
            val = obj.get(chave)
            if isinstance(val, str) and _URL_HTTP.match(val.strip()):
                return val.strip()[:500]
        for val in obj.values():
            encontrado = _extrair_url_pdf_de_objeto(val, profundidade + 1)
            if encontrado:
                return encontrado
    if isinstance(obj, list):
        for item in obj:
            encontrado = _extrair_url_pdf_de_objeto(item, profundidade + 1)
            if encontrado:
                return encontrado
    return ""


def _resposta_e_pdf_bruto(resp: requests.Response) -> bytes | None:
    if not resp.content or len(resp.content) < 200:
        return None
    if resp.content[:4] == b"%PDF":
        return resp.content
    ct = (resp.headers.get("Content-Type") or "").lower()
    if "pdf" in ct or "octet-stream" in ct:
        return resp.content
    return None


def buscar_pdf_bytes_memed(prescritor_id: str, prescricao_id: str) -> bytes | None:
    """Baixa o PDF bruto da API Memed (endpoint /pdf ou link direto)."""
    prescricao_id = (prescricao_id or "").strip()
    prescritor_id = (prescritor_id or "").strip()
    if not prescricao_id or not prescritor_id:
        return None

    token = _obter_token_prescritor(prescritor_id)
    if not token:
        return None

    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    base = endpoints["api"]
    headers_json = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/json",
    }
    headers_pdf = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/pdf,*/*",
    }
    params = {"api-key": api_key, "secret-key": secret_key}

    caminhos_pdf = [
        f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}/pdf",
        f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}/link",
    ]
    for path in caminhos_pdf:
        try:
            resp = requests.get(path, headers=headers_pdf, params=params, timeout=30)
            if not resp.ok:
                continue
            pdf = _resposta_e_pdf_bruto(resp)
            if pdf:
                return pdf
            try:
                url = _extrair_url_pdf_de_objeto(resp.json())
            except ValueError:
                url = ""
            if url:
                pdf = _baixar_pdf_url_permitida(url)
                if pdf:
                    return pdf
        except requests.RequestException as exc:
            logger.debug("Memed PDF bytes %s: %s", path, exc)

    caminho_meta = f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}"
    try:
        resp = requests.get(caminho_meta, headers=headers_json, params=params, timeout=20)
        if resp.ok:
            url = _extrair_url_pdf_de_objeto(resp.json())
            if url:
                return _baixar_pdf_url_permitida(url)
    except requests.RequestException as exc:
        logger.debug("Memed PDF meta %s: %s", caminho_meta, exc)
    return None


def buscar_pdf_url_memed(prescritor_id: str, prescricao_id: str) -> str:
    """Consulta a API Memed para obter URL do PDF da prescrição."""
    prescricao_id = (prescricao_id or "").strip()
    prescritor_id = (prescritor_id or "").strip()
    if not prescricao_id or not prescritor_id:
        return ""

    token = _obter_token_prescritor(prescritor_id)
    if not token:
        return ""

    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    base = endpoints["api"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/json",
    }
    params = {"api-key": api_key, "secret-key": secret_key}

    caminhos = [
        f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}",
        f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}/link",
        f"{base}/sinapse-prescricao/prescricoes/{prescricao_id}/pdf",
    ]
    for path in caminhos:
        try:
            resp = requests.get(path, headers=headers, params=params, timeout=20)
            if not resp.ok:
                continue
            url = _extrair_url_pdf_de_objeto(resp.json())
            if url and url_pdf_permitida(url):
                return url
        except (requests.RequestException, ValueError) as exc:
            logger.debug("Memed PDF %s: %s", path, exc)
    return ""


def arquivar_pdf_bytes_media(loja, conteudo: bytes, patient=None) -> str:
    """Envia bytes de PDF ao servidor de mídia ({paciente}/pdf/). Retorna URL ou vazio."""
    if not conteudo or len(conteudo) < 200 or conteudo[:4] != b"%PDF":
        return ""
    try:
        folder = folder_media_paciente("pdf", patient)
        return (
            media_upload(loja, conteudo, filename="prescricao.pdf", folder=folder) or ""
        ).strip()
    except Exception as exc:
        logger.warning("Falha ao arquivar bytes PDF Memed no servidor de mídia: %s", exc)
        return ""


def arquivar_pdf_media(loja, pdf_url: str, patient=None) -> str:
    """Baixa o PDF da Memed e salva no servidor de mídia ({paciente}/pdf/).

    Só baixa URL da allowlist. Se o arquivo já estiver no Magalu, devolve a URL.
    """
    url = (pdf_url or "").strip()
    if not url_pdf_permitida(url):
        return ""
    if is_media_url(url):
        return url
    try:
        conteudo = _baixar_pdf_url_permitida(url)
        if not conteudo:
            return url
        folder = folder_media_paciente("pdf", patient)
        arquivada = media_upload(loja, conteudo, filename="prescricao.pdf", folder=folder)
        return (arquivada or url).strip()
    except Exception as exc:
        logger.warning("Falha ao arquivar PDF Memed no servidor de mídia: %s", exc)
        return url


def resolver_pdf_prescricao(
    loja,
    professional,
    prescricao_id: str,
    pdf_url_frontend: str = "",
    patient=None,
) -> str:
    """Define URL final do PDF: frontend (allowlist) → API Memed → mídia."""
    pdf = (pdf_url_frontend or "").strip()[:500]
    if pdf and url_pdf_permitida(pdf):
        return arquivar_pdf_media(loja, pdf, patient=patient) or pdf

    prescritor = resolver_prescritor_id_profissional(professional) if prescricao_id else None
    if prescritor:
        pdf_bytes = buscar_pdf_bytes_memed(prescritor, prescricao_id)
        if pdf_bytes:
            arquivada = arquivar_pdf_bytes_media(loja, pdf_bytes, patient=patient)
            if arquivada:
                return arquivada

        pdf_url = buscar_pdf_url_memed(prescritor, prescricao_id)
        if pdf_url and url_pdf_permitida(pdf_url):
            return arquivar_pdf_media(loja, pdf_url, patient=patient) or pdf_url
    return ""
