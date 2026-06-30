"""Utilitários para resolver loja por slug ou atalho (URL amigável)."""
from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AbstractBaseUser

from .models import Loja


def resolve_loja_by_slug_or_atalho(
    identifier: str,
    *,
    owner: Optional[AbstractBaseUser] = None,
    is_active: bool = True,
    select_related: tuple[str, ...] = ('plano',),
) -> Optional[Loja]:
    """
    Busca loja pelo slug real (ex.: CPF) ou pelo atalho (ex.: beleza).
    Usado em rotas /loja/{slug}/... quando a URL pode ser atalho ou slug.
    """
    key = (identifier or '').strip().lower()
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


def invalidate_loja_info_publica_cache(loja) -> None:
    """Limpa cache Redis de info_publica (slug e atalho) após mudar is_blocked."""
    if not loja:
        return
    try:
        from django.core.cache import cache

        keys = set()
        for raw in (getattr(loja, 'slug', None), getattr(loja, 'atalho', None)):
            key = (raw or '').strip().lower()
            if key:
                keys.add(f'loja_info_publica_v4:{key}')
        for cache_key in keys:
            cache.delete(cache_key)
    except Exception:
        pass
