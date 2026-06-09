"""Busca textual ignorando acentos (via regex no PostgreSQL)."""
from __future__ import annotations

import re

from django.db.models import Q

# Cada letra com acento comum em português casa com a variante sem acento.
_ACCENT_CHAR_CLASS = {
    'a': '[aáàâãäAÁÀÂÃÄ]',
    'e': '[eéèêëEÉÈÊË]',
    'i': '[iíìîïIÍÌÎÏ]',
    'o': '[oóòôõöOÓÒÔÕÖ]',
    'u': '[uúùûüUÚÙÛÜ]',
    'c': '[cçCÇ]',
    'n': '[nñÑ]',
}


def termo_para_iregex_sem_acento(term: str) -> str:
    """
    Converte termo de busca em padrão regex case-insensitive que ignora acentos.
    Ex.: "livia" encontra "LÍVIA", "Lívia", "LIVIA".
    """
    term = (term or '').strip()
    if not term:
        return ''

    parts: list[str] = []
    for ch in term:
        if ch.isspace():
            parts.append(r'\s+')
            continue
        mapped = _ACCENT_CHAR_CLASS.get(ch.lower())
        if mapped:
            parts.append(mapped)
        else:
            parts.append(re.escape(ch))
    return ''.join(parts)


def q_icontains_sem_acento(term: str, *field_names: str) -> Q:
    """
    Q object OR entre campos, com contains ignorando acentos.
    Campos vazios ou termo curto demais retornam Q() vazio.
    """
    pattern = termo_para_iregex_sem_acento(term)
    if not pattern or not field_names:
        return Q()

    combined = Q()
    for field in field_names:
        combined |= Q(**{f'{field}__iregex': pattern})
    return combined
