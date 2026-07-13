"""Utilitários para resolver loja por slug ou atalho (URL amigável)."""
from __future__ import annotations

import time
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from .models import Loja

# Bump ao mudar o payload de info_publica (invalida entradas antigas no Redis).
INFO_PUBLICA_CACHE_PREFIX = "loja_info_publica_v5"
# Prefixos legados ainda podem existir até expirar o TTL.
_INFO_PUBLICA_CACHE_PREFIXES_LEGACY = ("loja_info_publica_v4",)
_INFO_PUBLICA_GEN_PREFIX = "loja_info_publica_gen"
INFO_PUBLICA_CACHE_TTL = 300


def resolve_loja_by_slug_or_atalho(
    identifier: str,
    *,
    owner: AbstractBaseUser | None = None,
    is_active: bool = True,
    select_related: tuple[str, ...] = ("plano",),
) -> Loja | None:
    """Busca loja pelo slug real (ex.: CPF) ou pelo atalho (ex.: beleza).
    Usado em rotas /loja/{slug}/... quando a URL pode ser atalho ou slug.
    """
    key = (identifier or "").strip().lower()
    if not key:
        return None

    qs = Loja.objects.all()
    if is_active:
        qs = qs.filter(is_active=True)
    if owner is not None:
        qs = qs.filter(owner=owner)
    if select_related:
        qs = qs.select_related(*select_related)

    loja = qs.filter(slug__iexact=key).first()
    if loja:
        return loja
    return qs.filter(atalho__iexact=key).first()


def info_publica_cache_identifiers(loja) -> set[str]:
    """Identificadores usados como chave de cache (slug + atalho)."""
    ids: set[str] = set()
    for raw in (getattr(loja, "slug", None), getattr(loja, "atalho", None)):
        key = (raw or "").strip().lower()
        if key:
            ids.add(key)
    return ids


def _info_publica_gen_key(loja_id: int | str) -> str:
    return f"{_INFO_PUBLICA_GEN_PREFIX}:{loja_id}"


def get_loja_info_publica_cached(slug: str) -> dict[str, Any] | None:
    """Lê cache de info_publica. Descarta entrada se for anterior à última invalidação
    (evita race: request antigo regrava cor antiga após salvar nova).
    """
    key = (slug or "").strip().lower()
    if not key:
        return None
    try:
        from django.core.cache import cache

        cached = cache.get(f"{INFO_PUBLICA_CACHE_PREFIX}:{key}")
        if not isinstance(cached, dict):
            return None
        loja_id = cached.get("id")
        cache_ts = cached.get("_cache_ts")
        if loja_id is not None and cache_ts is not None:
            gen = cache.get(_info_publica_gen_key(loja_id))
            if gen is not None and float(cache_ts) < float(gen):
                return None
        # Não expor metadados internos na API.
        return {k: v for k, v in cached.items() if not str(k).startswith("_")}
    except Exception:
        return None


def set_loja_info_publica_cache(
    loja,
    data: dict[str, Any],
    ttl: int = INFO_PUBLICA_CACHE_TTL,
) -> None:
    """Grava o mesmo payload sob slug e atalho (evita cache divergente)."""
    if not loja or not data:
        return
    try:
        from django.core.cache import cache

        payload = {**data, "_cache_ts": time.time()}
        for ident in info_publica_cache_identifiers(loja):
            cache.set(f"{INFO_PUBLICA_CACHE_PREFIX}:{ident}", payload, ttl)
    except Exception:
        pass


def invalidate_loja_info_publica_cache(loja) -> None:
    """Limpa cache Redis de info_publica (slug e atalho) após mudar cores/bloqueio."""
    if not loja:
        return
    try:
        from django.core.cache import cache

        idents = info_publica_cache_identifiers(loja)
        prefixes = (INFO_PUBLICA_CACHE_PREFIX, *_INFO_PUBLICA_CACHE_PREFIXES_LEGACY)
        for ident in idents:
            for prefix in prefixes:
                cache.delete(f"{prefix}:{ident}")
        loja_id = getattr(loja, "id", None)
        if loja_id is not None:
            # Qualquer SET em voo com dados antigos fica inválido.
            cache.set(_info_publica_gen_key(loja_id), time.time(), 86400)
    except Exception:
        pass


def rebuild_loja_info_publica_cache(loja) -> None:
    """Reconstrói o cache de info_publica imediatamente após salvar alterações.
    Garante que o próximo request (ex.: reload do frontend) pegue os dados novos.
    """
    if not loja:
        return
    try:
        from superadmin.views.loja.viewset import LojaViewSet
        tipo = getattr(loja, "tipo_loja", None)
        if tipo is None and hasattr(loja, "tipo_loja_id") and loja.tipo_loja_id:
            loja = Loja.objects.select_related("tipo_loja").get(pk=loja.pk)
        data = LojaViewSet._build_info_publica_data(loja, getattr(loja, "slug", "") or "")
        set_loja_info_publica_cache(loja, data, ttl=INFO_PUBLICA_CACHE_TTL)
    except Exception:
        pass
