"""Helpers e constantes de segurança (importados por settings de produção).
"""
from __future__ import annotations

import re

SLUG_VALIDATION_REGEX = re.compile(r"^[a-z0-9-]+$")

GENERIC_AUTH_ERROR_MESSAGE = "Credenciais inválidas"


def validate_store_slug(slug: str) -> bool:
    if not slug:
        raise ValueError("Slug não pode ser vazio")
    slug = str(slug).strip().lower()
    if len(slug) < 3:
        raise ValueError("Slug deve ter no mínimo 3 caracteres")
    if len(slug) > 50:
        raise ValueError("Slug deve ter no máximo 50 caracteres")
    if not SLUG_VALIDATION_REGEX.match(slug):
        raise ValueError("Slug deve conter apenas letras minúsculas, números e hífens")
    if slug.startswith("-") or slug.endswith("-"):
        raise ValueError("Slug não pode começar ou terminar com hífen")
    if "--" in slug:
        raise ValueError("Slug não pode conter hífens consecutivos")
    return True
