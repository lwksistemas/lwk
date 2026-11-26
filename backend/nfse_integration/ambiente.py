"""Resolução do ambiente NFS-e (produção vs homologação)."""
from __future__ import annotations

from typing import Any


def _explicito(config: Any, *attrs: str) -> str:
    for attr in attrs:
        valor = (getattr(config, attr, "") or "").strip()
        if valor in ("producao", "homologacao"):
            return valor
    return ""


def ambiente_nacional_loja(config: Any) -> str:
    """Ambiente da nota da loja/CRM.

    Prioridade: ``nacional_ambiente`` explícito → flag ISSNet de homologação →
    ``issnet_ambiente`` legado → produção (CRM em produção não tem campo nacional).
    """
    explicito = _explicito(config, "nacional_ambiente", "issnet_ambiente")
    if explicito:
        return explicito
    if getattr(config, "issnet_ambiente_homologacao", False):
        return "homologacao"
    return "producao"


def ambiente_nacional_superadmin(config: Any) -> str:
    """Ambiente do superadmin: vazio cai em homologação (não emite em produção por engano)."""
    return _explicito(config, "nacional_ambiente", "issnet_ambiente") or "homologacao"
