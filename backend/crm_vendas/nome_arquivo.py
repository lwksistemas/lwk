"""Nome de download só com letras, números, ponto, hífen e sublinhado."""
from __future__ import annotations

import re

_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


def nome_arquivo_download(*partes: object, extensao: str) -> str:
    bruto = "_".join(str(parte) for parte in partes if parte is not None and str(parte) != "")
    limpo = _SEGURO.sub("_", bruto).strip("._")[:100] or "documento"
    ext = _SEGURO.sub("", (extensao or "pdf").lstrip(".").lower()) or "pdf"
    return f"{limpo}.{ext}"
