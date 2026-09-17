"""Helpers compartilhados do parser de catálogo (CSV e PDF)."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

CATALOGO_PDF_MAX_BYTES = 8 * 1024 * 1024


def _parse_preco(raw: str) -> Decimal:
    s = (raw or "").strip().replace("R$", "").replace(" ", "")
    if not s:
        return Decimal("0.00")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def _norm_nome(nome: str) -> str:
    nfd = unicodedata.normalize("NFD", (nome or "").strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _codigo_de_nome(nome: str) -> str:
    nfd = unicodedata.normalize("NFD", nome)
    ascii_txt = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_txt).strip("-").upper()
    return (slug[:40] or "PROD").rstrip("-")
