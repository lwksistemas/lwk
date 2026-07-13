"""Utilitários para resolver loja por slug ou atalho (URL amigável)."""
from __future__ import annotations

import time
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from .models import Loja

# Bump ao mudar o payload de info_publica (invalida entradas antigas no Redis).
INFO_PUBLICA_CACHE_PREFIX = 'loja_info_publica_v5'
# Prefixos legados ainda podem existir até expirar o TTL.
_INFO_PUBLICA_CACHE_PREFIXES_LEGACY = ('loja_info_publica_v4',)
_INFO_PUBLICA_GEN_PREFIX = 'loja_info_publica_gen'
INFO_PUBLICA_CACHE_TTL = 300


def resolve_loja_by_slug_or_atalho(
    identifier: str,
    *,
    owner: AbstractBaseUser | None = None,
    is_active: bool = True,
    select_related: tuple[str, ...] = ('plano',),
) -> Loja | None:
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


def info_publica_cache_identifiers(loja) -> set[str]:
    """Identificadores usados como chave de cache (slug + atalho)."""
    ids: set[str] = set()
    for raw in (getattr(loja, 'slug', None), getattr(loja, 'atalho', None)):
        key = (raw or '').strip().lower()
        if key:
            ids.add(key)
    return ids


def _info_publica_gen_key(loja_id: int | str) -> str:
    return f'{_INFO_PUBLICA_GEN_PREFIX}:{loja_id}'


def get_loja_info_publica_cached(slug: str) -> dict[str, Any] | None:
    """
    Lê cache de info_publica. Descarta entrada se for anterior à última invalidação
    (evita race: request antigo regrava cor antiga após salvar nova).
    """
    key = (slug or '').strip().lower()
    if not key:
        return None
    try:
        from django.core.cache import cache

        cached = cache.get(f'{INFO_PUBLICA_CACHE_PREFIX}:{key}')
        if not isinstance(cached, dict):
            return None
        loja_id = cached.get('id')
        cache_ts = cached.get('_cache_ts')
        if loja_id is not None and cache_ts is not None:
            gen = cache.get(_info_publica_gen_key(loja_id))
            if gen is not None and float(cache_ts) < float(gen):
                return None
        # Não expor metadados internos na API.
        return {k: v for k, v in cached.items() if not str(k).startswith('_')}
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

        payload = {**data, '_cache_ts': time.time()}
        for ident in info_publica_cache_identifiers(loja):
            cache.set(f'{INFO_PUBLICA_CACHE_PREFIX}:{ident}', payload, ttl)
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
                cache.delete(f'{prefix}:{ident}')
        loja_id = getattr(loja, 'id', None)
        if loja_id is not None:
            # Qualquer SET em voo com dados antigos fica inválido.
            cache.set(_info_publica_gen_key(loja_id), time.time(), 86400)
    except Exception:
        pass


def rebuild_loja_info_publica_cache(loja) -> None:
    """
    Reconstrói o cache de info_publica imediatamente após salvar alterações.
    Garante que o próximo request (ex.: reload do frontend) pegue os dados novos.
    """
    if not loja:
        return
    try:
        import re

        tipo = getattr(loja, 'tipo_loja', None)
        if tipo is None and hasattr(loja, 'tipo_loja_id') and loja.tipo_loja_id:
            loja = Loja.objects.select_related('tipo_loja').get(pk=loja.pk)
            tipo = loja.tipo_loja

        tipo_nome = tipo.nome if tipo else 'Loja'
        cor_primaria_loja = (getattr(loja, 'cor_primaria', None) or '').strip()
        cor_secundaria_loja = (getattr(loja, 'cor_secundaria', None) or '').strip()
        cor_primaria_tipo = (getattr(tipo, 'cor_primaria', None) or '').strip() if tipo else ''
        cor_secundaria_tipo = (getattr(tipo, 'cor_secundaria', None) or '').strip() if tipo else ''
        cor_primaria = cor_primaria_loja or cor_primaria_tipo or '#10B981'
        cor_secundaria = cor_secundaria_loja or cor_secundaria_tipo or '#059669'

        cidade = getattr(loja, 'cidade', '') or ''
        uf = getattr(loja, 'uf', '') or ''
        cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
        endereco_parts = [
            getattr(loja, 'logradouro', '') or '',
            getattr(loja, 'numero', '') or '',
            getattr(loja, 'complemento', '') or '',
            getattr(loja, 'bairro', '') or '',
            cidade_uf,
            f"CEP {loja.cep}" if getattr(loja, 'cep', '') else '',
        ]
        endereco = ', '.join(p for p in endereco_parts if p).strip() or None

        cpf_cnpj_raw = (getattr(loja, 'cpf_cnpj', '') or '').strip()
        cpf_cnpj_digits = re.sub(r'\D', '', cpf_cnpj_raw)
        if len(cpf_cnpj_digits) not in (11, 14):
            slug_digits = re.sub(r'\D', '', getattr(loja, 'slug', '') or '')
            if len(slug_digits) in (11, 14):
                cpf_cnpj_digits = slug_digits

        data = {
            'id': loja.id,
            'nome': getattr(loja, 'nome', '') or '',
            'slug': getattr(loja, 'slug', '') or '',
            'atalho': getattr(loja, 'atalho', '') or '',
            'tipo_loja_nome': tipo_nome,
            'cor_primaria': cor_primaria,
            'cor_secundaria': cor_secundaria,
            'cor_fundo_pagina': (getattr(loja, 'cor_fundo_pagina', None) or '').strip(),
            'agenda_status_colors': getattr(loja, 'agenda_status_colors', None) or {},
            'logo': getattr(loja, 'logo', None) or '',
            'login_background': getattr(loja, 'login_background', None) or '',
            'login_logo': getattr(loja, 'login_logo', None) or '',
            'login_page_url': getattr(loja, 'login_page_url', None) or '',
            'senha_foi_alterada': getattr(loja, 'senha_foi_alterada', False),
            'requer_cpf_cnpj': False,
            'endereco': endereco,
            'cpf_cnpj': cpf_cnpj_digits,
            'is_blocked': bool(getattr(loja, 'is_blocked', False)),
        }
        set_loja_info_publica_cache(loja, data, ttl=INFO_PUBLICA_CACHE_TTL)
    except Exception:
        pass
