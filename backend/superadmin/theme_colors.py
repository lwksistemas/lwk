"""Helpers para cores de identidade visual da loja (agenda + marca)."""
from __future__ import annotations

import re
from typing import Any

_HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')

AGENDA_STATUS_COLOR_KEYS = (
    'SCHEDULED',
    'CLIENT_CONFIRMED',
    'PHONE_CONFIRMED',
    'CONFIRMED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    'NO_SHOW',
)


def normalize_hex_color(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    val = value.strip()
    if _HEX_RE.match(val):
        return val.lower()
    if re.match(r'^#[0-9A-Fa-f]{3}$', val):
        return '#' + ''.join(c * 2 for c in val[1:]).lower()
    return None


def sanitize_agenda_status_colors(raw: Any) -> dict:
    """
    Aceita dict { STATUS: { bg, border } } e devolve só chaves/valores válidos.
    PENDING é alias de SCHEDULED — não persiste separado.
    """
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key in AGENDA_STATUS_COLOR_KEYS:
        entry = raw.get(key)
        if not isinstance(entry, dict):
            continue
        bg = normalize_hex_color(entry.get('bg'))
        border = normalize_hex_color(entry.get('border'))
        if bg and border:
            out[key] = {'bg': bg, 'border': border}
    return out
