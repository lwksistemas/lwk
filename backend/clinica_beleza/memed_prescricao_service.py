"""Busca e arquiva PDFs de prescrições emitidas na Memed."""
from __future__ import annotations

import logging
import re
from typing import Any

import requests

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
        except requests.RequestException as exc:
            logger.debug('Memed PDF %s: %s', path, exc)
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
        slug = (getattr(loja, 'atalho', None) or loja.slug or str(loja.id)).strip().lower()
        folder = f'lwksistemas/{slug}/clinica-beleza/prescricoes-memed'
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
    """Define URL final do PDF: frontend → API Memed → arquivamento Cloudinary."""
    pdf = (pdf_url_frontend or '').strip()[:500]
    if not pdf and prescricao_id:
        prescritor = resolver_prescritor_id_profissional(professional)
        if prescritor:
            pdf = buscar_pdf_url_memed(prescritor, prescricao_id)
    if pdf:
        pdf = arquivar_pdf_cloudinary(loja, pdf)
    return pdf
