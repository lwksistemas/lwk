"""Busca e arquiva PDFs de prescrições emitidas na Memed."""
from __future__ import annotations

import logging
import re
from typing import Any

import requests

from core.cloudinary_folders import loja_clinica_memed
from .memed_config import memed_config as _memed_config, memed_credentials as _memed_credentials

logger = logging.getLogger(__name__)

_URL_HTTP = re.compile(r'^https?://', re.I)


def resolver_prescritor_id_profissional(professional) -> str | None:
    """CPF ou registro+UF do profissional para a API Memed."""
    if not professional:
        return None
    cpf = ''.join(ch for ch in (getattr(professional, 'cpf', '') or '') if ch.isdigit())
    if len(cpf) == 11:
        return cpf
    raw = (getattr(professional, 'registro_profissional', '') or '').strip().upper()
    if not raw:
        return None
    match_uf = re.search(r'[-\s/]*([A-Z]{2})\s*$', raw)
    uf = match_uf.group(1) if match_uf else (getattr(professional, 'conselho_uf', '') or '').strip().upper()
    registro = ''.join(ch for ch in raw if ch.isalnum())
    if uf and registro.endswith(uf):
        registro = registro[: -len(uf)]
    if registro:
        return f'{registro}{uf}' if uf else registro
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
            params={'api-key': api_key, 'secret-key': secret_key},
            headers={'Accept': 'application/vnd.api+json', 'Content-Type': 'application/json'},
            timeout=15,
        )
        if not resp.ok:
            logger.warning('Memed token prescritor %s: HTTP %s', prescritor_id, resp.status_code)
            return None
        return ((resp.json() or {}).get('data') or {}).get('attributes', {}).get('token')
    except requests.RequestException as exc:
        logger.warning('Memed token prescritor %s: %s', prescritor_id, exc)
        return None


def _extrair_url_pdf_de_objeto(obj: Any, profundidade: int = 0) -> str:
    if profundidade > 8 or obj is None:
        return ''
    if isinstance(obj, str):
        s = obj.strip()
        if _URL_HTTP.match(s) and ('.pdf' in s.lower() or 'memed' in s.lower() or 'prescri' in s.lower()):
            return s[:500]
        return ''
    if isinstance(obj, dict):
        for chave in (
            'url_pdf', 'pdf_url', 'link_pdf', 'pdf', 'url', 'link',
            'secure_url', 'download_url', 'arquivo_url',
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
    return ''


def _resposta_e_pdf_bruto(resp: requests.Response) -> bytes | None:
    if not resp.content or len(resp.content) < 200:
        return None
    if resp.content[:4] == b'%PDF':
        return resp.content
    ct = (resp.headers.get('Content-Type') or '').lower()
    if 'pdf' in ct or 'octet-stream' in ct:
        return resp.content
    return None


def buscar_pdf_bytes_memed(prescritor_id: str, prescricao_id: str) -> bytes | None:
    """Baixa o PDF bruto da API Memed (endpoint /pdf ou link direto)."""
    prescricao_id = (prescricao_id or '').strip()
    prescritor_id = (prescritor_id or '').strip()
    if not prescricao_id or not prescritor_id:
        return None

    token = _obter_token_prescritor(prescritor_id)
    if not token:
        return None

    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    base = endpoints['api']
    headers_json = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/json',
    }
    headers_pdf = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/pdf,*/*',
    }
    params = {'api-key': api_key, 'secret-key': secret_key}

    caminhos_pdf = [
        f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}/pdf',
        f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}/link',
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
                url = ''
            if url:
                resp_arquivo = requests.get(url, timeout=45, headers={'User-Agent': 'LWK-Sistemas/1.0'})
                if resp_arquivo.ok:
                    pdf = _resposta_e_pdf_bruto(resp_arquivo)
                    if pdf:
                        return pdf
        except requests.RequestException as exc:
            logger.debug('Memed PDF bytes %s: %s', path, exc)

    caminho_meta = f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}'
    try:
        resp = requests.get(caminho_meta, headers=headers_json, params=params, timeout=20)
        if resp.ok:
            url = _extrair_url_pdf_de_objeto(resp.json())
            if url:
                resp_arquivo = requests.get(url, timeout=45, headers={'User-Agent': 'LWK-Sistemas/1.0'})
                if resp_arquivo.ok:
                    return _resposta_e_pdf_bruto(resp_arquivo)
    except requests.RequestException as exc:
        logger.debug('Memed PDF meta %s: %s', caminho_meta, exc)
    return None


def buscar_pdf_url_memed(prescritor_id: str, prescricao_id: str) -> str:
    """Consulta a API Memed para obter URL do PDF da prescrição."""
    prescricao_id = (prescricao_id or '').strip()
    prescritor_id = (prescritor_id or '').strip()
    if not prescricao_id or not prescritor_id:
        return ''

    token = _obter_token_prescritor(prescritor_id)
    if not token:
        return ''

    env, endpoints = _memed_config()
    api_key, secret_key = _memed_credentials(env)
    base = endpoints['api']
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/json',
    }
    params = {'api-key': api_key, 'secret-key': secret_key}

    caminhos = [
        f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}',
        f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}/link',
        f'{base}/sinapse-prescricao/prescricoes/{prescricao_id}/pdf',
    ]
    for path in caminhos:
        try:
            resp = requests.get(path, headers=headers, params=params, timeout=20)
            if not resp.ok:
                continue
            url = _extrair_url_pdf_de_objeto(resp.json())
            if url:
                return url
        except (requests.RequestException, ValueError) as exc:
            logger.debug('Memed PDF %s: %s', path, exc)
    return ''


def arquivar_pdf_bytes_cloudinary(loja, conteudo: bytes) -> str:
    """Envia bytes de PDF ao Cloudinary da loja. Retorna URL ou vazio."""
    if not conteudo or len(conteudo) < 200 or conteudo[:4] != b'%PDF':
        return ''
    try:
        import cloudinary.uploader
        from superadmin.cloudinary_models import CloudinaryConfig

        cfg = CloudinaryConfig.get_config()
        if not cfg.enabled or not cfg.cloud_name or not cfg.api_key or not cfg.api_secret:
            return ''
        import cloudinary
        cloudinary.config(
            cloud_name=cfg.cloud_name,
            api_key=cfg.api_key,
            api_secret=cfg.api_secret,
            secure=True,
        )
        folder = loja_clinica_memed(loja)
        resultado = cloudinary.uploader.upload(
            conteudo,
            folder=folder,
            resource_type='raw',
            format='pdf',
        )
        return (resultado.get('secure_url') or '').strip()
    except Exception as exc:
        logger.warning('Falha ao arquivar bytes PDF Memed no Cloudinary: %s', exc)
        return ''


def arquivar_pdf_cloudinary(loja, pdf_url: str) -> str:
    """
    Baixa o PDF da Memed e salva no Cloudinary da loja.
    Retorna URL arquivada ou a original se falhar.
    """
    url = (pdf_url or '').strip()
    if not url or not _URL_HTTP.match(url):
        return ''

    try:
        resp = requests.get(url, timeout=45, headers={'User-Agent': 'LWK-Sistemas/1.0'})
        resp.raise_for_status()
        conteudo = resp.content
    except requests.RequestException as exc:
        logger.warning('Falha ao baixar PDF Memed: %s', exc)
        return url

    if len(conteudo) < 200:
        return url

    try:
        import cloudinary.uploader
        from superadmin.cloudinary_models import CloudinaryConfig

        cfg = CloudinaryConfig.get_config()
        if not cfg.enabled or not cfg.cloud_name or not cfg.api_key or not cfg.api_secret:
            return url
        import cloudinary
        cloudinary.config(
            cloud_name=cfg.cloud_name,
            api_key=cfg.api_key,
            api_secret=cfg.api_secret,
            secure=True,
        )
        folder = loja_clinica_memed(loja)
        resultado = cloudinary.uploader.upload(
            conteudo,
            folder=folder,
            resource_type='raw',
            format='pdf',
        )
        arquivada = (resultado.get('secure_url') or '').strip()
        return arquivada or url
    except Exception as exc:
        logger.warning('Falha ao arquivar PDF Memed no Cloudinary: %s', exc)
        return url


def resolver_pdf_prescricao(loja, professional, prescricao_id: str, pdf_url_frontend: str = '') -> str:
    """Define URL final do PDF: frontend → API Memed (bytes ou URL) → Cloudinary."""
    pdf = (pdf_url_frontend or '').strip()[:500]
    if pdf:
        return arquivar_pdf_cloudinary(loja, pdf) or pdf

    prescritor = resolver_prescritor_id_profissional(professional) if prescricao_id else None
    if prescritor:
        pdf_bytes = buscar_pdf_bytes_memed(prescritor, prescricao_id)
        if pdf_bytes:
            arquivada = arquivar_pdf_bytes_cloudinary(loja, pdf_bytes)
            if arquivada:
                return arquivada

        pdf_url = buscar_pdf_url_memed(prescritor, prescricao_id)
        if pdf_url:
            return arquivar_pdf_cloudinary(loja, pdf_url) or pdf_url
    return ''
