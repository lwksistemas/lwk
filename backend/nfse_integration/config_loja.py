"""Configuração de NFS-e da loja, registrada pelo próprio app.

O motor de emissão não importa a clínica nem o CRM. Cada app, ao subir,
registra como achar a config do seu tipo de loja.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Tipos cuja nota fica na tabela da clínica da beleza (também o salão).
TIPOS_CONFIG_CLINICA = frozenset({"CLIEST", "CLIBEL", "CABEL"})

Getter = Callable[[Any], Any]

_por_tipo: dict[str, Getter] = {}
_padrao: Getter | None = None


def registrar_config_nfse_tipos(tipos: frozenset[str], getter: Getter) -> None:
    for tipo in tipos:
        _por_tipo[str(tipo).strip()] = getter


def registrar_config_nfse_padrao(getter: Getter) -> None:
    global _padrao
    _padrao = getter


def tipo_codigo_loja(loja: Any) -> str:
    tipo = getattr(loja, "tipo_loja", None)
    if tipo is None:
        return ""
    return (getattr(tipo, "codigo", "") or "").strip()


def config_nfse_da_loja(loja: Any) -> Any:
    getter = _por_tipo.get(tipo_codigo_loja(loja)) or _padrao
    if getter is None:
        raise RuntimeError("Nenhum app registrou a configuração de NFS-e.")
    return getter(loja)


def config_nfse_por_loja_id(loja_id: int) -> Any:
    from superadmin.models import Loja

    loja = (
        Loja.objects.using("default")
        .filter(id=loja_id)
        .select_related("tipo_loja")
        .first()
    )
    if loja is not None:
        return config_nfse_da_loja(loja)
    if _padrao is None:
        raise RuntimeError("Nenhum app registrou a configuração de NFS-e.")

    class _SemCadastro:
        id = loja_id
        tipo_loja = None

    return _padrao(_SemCadastro())
