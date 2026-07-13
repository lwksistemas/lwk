"""Pastas padronizadas no Cloudinary (raiz: lwksistemas).

Estrutura:
  lwksistemas/producao/superadmin/homepage
  lwksistemas/producao/superadmin/login
  lwksistemas/producao/suporte/login
  lwksistemas/producao/{cpf_cnpj}/login
  lwksistemas/producao/{cpf_cnpj}/clinica-beleza-fotos
  (mesma árvore em lwksistemas/beta/...)
"""
from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)

ROOT = "lwksistemas"


def _sanitize_segment(value: str | None) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9_-]+", "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw or "sem-identificador"


def ambiente_segment() -> str:
    """Beta (homologação) ou producao."""
    explicit = (os.environ.get("LWK_ENV") or os.environ.get("LWK_AMBIENTE") or "").strip().lower()
    if explicit in ("beta", "staging", "homologacao", "homologação"):
        return "beta"
    if explicit in ("producao", "production", "prod"):
        return "producao"
    frontend = (getattr(settings, "FRONTEND_URL", None) or "").lower()
    if "beta.lwksistemas.com.br" in frontend:
        return "beta"
    return "producao"


def resolve_ambiente_segment(origin_or_base: str | None = None) -> str:
    """beta/producao — prioriza hostname (ex.: beta.lwksistemas.com.br no QR)."""
    if origin_or_base:
        raw = origin_or_base.strip()
        if raw and "://" not in raw:
            raw = f'https://{raw.lstrip("/")}'
        host = (urlparse(raw).hostname or "").lower()
        if host == "beta.lwksistemas.com.br":
            return "beta"
        if host in ("lwksistemas.com.br", "www.lwksistemas.com.br"):
            return "producao"
    return ambiente_segment()


def _cpf_cnpj_digits(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) in (11, 14):
        return digits
    return ""


def loja_documento_segment(loja) -> str:
    """CPF/CNPJ só dígitos; slug numérico; fallback id interno (nunca atalho)."""
    digits = _cpf_cnpj_digits(getattr(loja, "cpf_cnpj", None))
    if digits:
        return digits
    slug_digits = _cpf_cnpj_digits(getattr(loja, "slug", None))
    if slug_digits:
        return slug_digits
    return _sanitize_segment(str(getattr(loja, "id", "")))


def loja_segment(loja) -> str:
    """Slug/atalho — apenas validação de uploads legados."""
    for attr in ("slug", "atalho"):
        valor = _sanitize_segment(getattr(loja, attr, None))
        if valor and valor != "sem-identificador":
            return valor
    return _sanitize_segment(str(getattr(loja, "id", "")))


def loja_segments_legacy(loja) -> list[str]:
    """Identificadores legados para validar uploads antigos."""
    vistos: list[str] = []
    doc = re.sub(r"\D", "", getattr(loja, "cpf_cnpj", None) or "")
    if doc and doc not in vistos:
        vistos.append(doc)
    for attr in ("atalho", "slug"):
        valor = _sanitize_segment(getattr(loja, attr, None))
        if valor and valor != "sem-identificador" and valor not in vistos:
            vistos.append(valor)
    id_seg = _sanitize_segment(str(getattr(loja, "id", "")))
    if id_seg and id_seg not in vistos:
        vistos.append(id_seg)
    return vistos


def _path(*parts: str) -> str:
    return "/".join([ROOT, *[p.strip("/") for p in parts if p]])


def superadmin_homepage() -> str:
    return _path(ambiente_segment(), "superadmin", "homepage")


def superadmin_login() -> str:
    return _path(ambiente_segment(), "superadmin", "login")


def suporte_root() -> str:
    return _path(ambiente_segment(), "suporte")


def suporte_login() -> str:
    return _path(ambiente_segment(), "suporte", "login")


def loja_root(loja) -> str:
    return _path(ambiente_segment(), loja_documento_segment(loja))


def loja_login(loja) -> str:
    return _path(ambiente_segment(), loja_documento_segment(loja), "login")


def loja_login_documento(cpf_cnpj: str) -> str:
    digits = re.sub(r"\D", "", cpf_cnpj or "")
    seg = digits or _sanitize_segment(cpf_cnpj)
    return _path(ambiente_segment(), seg, "login")


def loja_clinica_fotos(loja, ambiente: str | None = None) -> str:
    env = ambiente if ambiente in ("beta", "producao") else ambiente_segment()
    return _path(env, loja_documento_segment(loja), "clinica-beleza-fotos")


def loja_clinica_fotos_documento(cpf_cnpj: str) -> str:
    digits = re.sub(r"\D", "", cpf_cnpj or "")
    seg = digits or _sanitize_segment(cpf_cnpj)
    return _path(ambiente_segment(), seg, "clinica-beleza-fotos")


def loja_clinica_fotos_paths(loja) -> list[str]:
    paths: list[str] = []
    doc = loja_documento_segment(loja)
    for env in ("beta", "producao"):
        for p in (
            _path(env, doc, "clinica-beleza-fotos"),
            _path(env, doc, "login"),
            _path(env, doc),
        ):
            if p not in paths:
                paths.append(p)
    env = ambiente_segment()
    for seg in loja_segments_legacy(loja):
        legado = [
            f"{ROOT}/{env}/superadmin-homepage",
            f"{ROOT}/{env}/superadmin-login",
            f"{ROOT}/{env}/superadmin/homepage",
            f"{ROOT}/{env}/{seg}/clinica-beleza-fotos",
            f"{ROOT}/{env}/{seg}",
            f"{ROOT}/{seg}/clinica-beleza/fotos-paciente",
            f"{ROOT}/{env}/{seg}/clinica-beleza/fotos-paciente",
            f"{ROOT}/{seg}/login",
            f"{ROOT}/{env}/{seg}/login",
            f"{ROOT}/{seg}",
            f"{ROOT}/superadmin/homepage",
        ]
        for p in legado:
            if p not in paths:
                paths.append(p)
    return paths


def loja_clinica_memed(loja) -> str:
    return _path(ambiente_segment(), loja_documento_segment(loja), "clinica-beleza-memed")


def loja_prefixes(loja) -> list[str]:
    prefixes = [f"{loja_root(loja)}/", f"{loja_root(loja)}", f"{loja_login(loja)}/"]
    env = ambiente_segment()
    for seg in loja_segments_legacy(loja):
        for base in (
            f"{ROOT}/{env}/{seg}/",
            f"{ROOT}/{env}/{seg}",
            f"{ROOT}/{seg}/",
            f"{ROOT}/{seg}",
        ):
            if base not in prefixes:
                prefixes.append(base)
    return prefixes


def folders_for_new_loja(loja) -> list[str]:
    env = ambiente_segment()
    doc = loja_documento_segment(loja)
    loja_base = _path(env, doc)
    return [
        _path(env, "superadmin"),
        _path(env, "superadmin", "homepage"),
        _path(env, "superadmin", "login"),
        _path(env, "suporte"),
        _path(env, "suporte", "login"),
        loja_base,
        f"{loja_base}/login",
        f"{loja_base}/clinica-beleza-fotos",
        f"{loja_base}/clinica-beleza-memed",
    ]


def ensure_cloudinary_folders(folder_paths: list[str]) -> None:
    if not folder_paths:
        return
    try:
        import cloudinary.api

        from core.cloudinary_upload_preset import _configure_cloudinary_sdk

        if not _configure_cloudinary_sdk():
            return
        for path in folder_paths:
            try:
                cloudinary.api.create_folder(path)
                logger.info("Cloudinary: pasta criada %s", path)
            except Exception as exc:
                msg = str(exc).lower()
                if "already exists" in msg or "exist" in msg:
                    continue
                logger.debug("Cloudinary create_folder %s: %s", path, exc)
    except Exception as exc:
        logger.warning("Não foi possível criar pastas Cloudinary: %s", exc)


def ensure_loja_cloudinary_folders(loja) -> None:
    ensure_cloudinary_folders(folders_for_new_loja(loja))
