"""
Pastas padronizadas no Cloudinary (raiz: lwksistemas).

Estrutura:
  lwksistemas/superadmin/homepage   — site público (hero, módulos, funcionalidades)
  lwksistemas/superadmin/login      — telas de login superadmin / suporte
  lwksistemas/suporte               — chamados, erros, anexos de suporte
  lwksistemas/{loja}/login          — logo e fundo de login da loja
  lwksistemas/{loja}/clinica-beleza/... — demais mídias por app
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

ROOT = 'lwksistemas'


def _sanitize_segment(value: str | None) -> str:
    raw = (value or '').strip().lower()
    raw = re.sub(r'[^a-z0-9_-]+', '-', raw)
    raw = re.sub(r'-+', '-', raw).strip('-')
    return raw or 'sem-identificador'


def loja_segment(loja) -> str:
    """Identificador estável da loja na pasta (slug > atalho > id)."""
    for attr in ('slug', 'atalho'):
        valor = _sanitize_segment(getattr(loja, attr, None))
        if valor and valor != 'sem-identificador':
            return valor
    return _sanitize_segment(str(getattr(loja, 'id', '')))


def loja_segments_legacy(loja) -> list[str]:
    """Slug, atalho e id — para validar uploads antigos."""
    vistos: list[str] = []
    for attr in ('atalho', 'slug'):
        valor = _sanitize_segment(getattr(loja, attr, None))
        if valor and valor != 'sem-identificador' and valor not in vistos:
            vistos.append(valor)
    id_seg = _sanitize_segment(str(getattr(loja, 'id', '')))
    if id_seg and id_seg not in vistos:
        vistos.append(id_seg)
    return vistos


def superadmin_homepage() -> str:
    return f'{ROOT}/superadmin/homepage'


def superadmin_login() -> str:
    return f'{ROOT}/superadmin/login'


def suporte_root() -> str:
    return f'{ROOT}/suporte'


def suporte_login() -> str:
    return f'{suporte_root()}/login'


def loja_root(loja) -> str:
    return f'{ROOT}/{loja_segment(loja)}'


def loja_login(loja) -> str:
    return f'{loja_root(loja)}/login'


def loja_login_slug(slug: str) -> str:
    return f'{ROOT}/{_sanitize_segment(slug)}/login'


def loja_clinica_fotos(loja) -> str:
    return f'{loja_root(loja)}/clinica-beleza/fotos-paciente'


def loja_clinica_fotos_paths(loja) -> list[str]:
    return [f'{ROOT}/{seg}/clinica-beleza/fotos-paciente' for seg in loja_segments_legacy(loja)]


def loja_clinica_memed(loja) -> str:
    return f'{loja_root(loja)}/clinica-beleza/prescricoes-memed'


def loja_prefixes(loja) -> list[str]:
    """Prefixos válidos para mídia da loja (inclui legado sem subpasta)."""
    prefixes = [f'{loja_root(loja)}/']
    for seg in loja_segments_legacy(loja):
        legado = f'{ROOT}/{seg}/'
        if legado not in prefixes:
            prefixes.append(legado)
    return prefixes


def folders_for_new_loja(loja) -> list[str]:
    """Pastas criadas ao cadastrar uma loja."""
    base = loja_root(loja)
    return [
        base,
        f'{base}/login',
        f'{base}/clinica-beleza',
        f'{base}/clinica-beleza/fotos-paciente',
        f'{base}/clinica-beleza/prescricoes-memed',
    ]


def ensure_cloudinary_folders(folder_paths: list[str]) -> None:
    """Cria pastas no Cloudinary (ignora se já existirem ou API indisponível)."""
    if not folder_paths:
        return
    try:
        import cloudinary
        import cloudinary.api
        from superadmin.cloudinary_models import CloudinaryConfig

        cfg = CloudinaryConfig.get_config()
        if not cfg.enabled or not cfg.cloud_name or not cfg.api_key or not cfg.api_secret:
            return
        cloudinary.config(
            cloud_name=cfg.cloud_name,
            api_key=cfg.api_key,
            api_secret=cfg.api_secret,
            secure=True,
        )
        for path in folder_paths:
            try:
                cloudinary.api.create_folder(path)
                logger.info('Cloudinary: pasta criada %s', path)
            except Exception as exc:
                msg = str(exc).lower()
                if 'already exists' in msg or 'exist' in msg:
                    continue
                logger.debug('Cloudinary create_folder %s: %s', path, exc)
    except Exception as exc:
        logger.warning('Não foi possível criar pastas Cloudinary: %s', exc)


def ensure_loja_cloudinary_folders(loja) -> None:
    ensure_cloudinary_folders(folders_for_new_loja(loja))
