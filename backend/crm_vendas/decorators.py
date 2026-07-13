"""Decorators reutilizáveis para CRM Vendas.
Elimina código duplicado de cache em list() e bloqueio de vendedor.
"""
from functools import wraps

from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response

from tenants.middleware import ensure_loja_context, get_current_loja_id

from .cache import CRMCacheManager
from .utils import get_current_vendedor_id, is_vendedor_usuario


def cache_list_response(cache_prefix, ttl=120, extra_keys=None):
    """Decorator para cachear resposta de list().

    Gera chave de cache baseada em:
    - loja_id
    - vendedor_id (ou 'owner')
    - query params especificados em extra_keys
    - versão (para atividades)

    Args:
        cache_prefix: Prefixo do cache (ex: 'crm_contas_list')
        ttl: Tempo de vida do cache em segundos (padrão: 120)
        extra_keys: Lista de query params para incluir na chave (ex: ['data_inicio', 'data_fim'])

    Usage:
        @cache_list_response('crm_contas_list', ttl=120)
        def list(self, request, *args, **kwargs):
            return super().list(request, *args, **kwargs)

    Returns:
        Decorator function

    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            ensure_loja_context(request)
            loja_id = get_current_loja_id()
            vendedor_id = get_current_vendedor_id(request)

            # Construir kwargs para chave de cache
            cache_kwargs = {}
            if extra_keys:
                for key in extra_keys:
                    value = request.query_params.get(key)
                    if value:
                        cache_kwargs[key] = value

            # Incluir versão na chave para qualquer prefix que tenha versão mapeada
            # Isso invalida automaticamente todas as variações sem precisar de DB query
            version_map = CRMCacheManager._get_prefix_version_map()
            version_prefix = version_map.get(cache_prefix) or (
                CRMCacheManager.ATIVIDADES_VERSION
                if cache_prefix == CRMCacheManager.ATIVIDADES else None
            )
            if version_prefix and loja_id:
                vkey = CRMCacheManager.get_cache_key(version_prefix, loja_id)
                cache_kwargs["v"] = cache.get(vkey, 0)

            # Gerar chave de cache
            cache_key = CRMCacheManager.get_cache_key(
                cache_prefix,
                loja_id,
                vendedor_id,
                **cache_kwargs,
            )

            # Tentar obter do cache
            if cache_key:
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)

            # ✅ OTIMIZAÇÃO: Lock para evitar race condition
            # Quando cache é invalidado, múltiplas requisições simultâneas podem
            # retornar lista vazia. Lock garante que apenas uma busque do BD.
            lock_key = f"{cache_key}:lock"
            lock_acquired = cache.add(lock_key, "1", timeout=10)

            if not lock_acquired:
                # Outra requisição está buscando, aguardar um pouco
                import time
                time.sleep(0.1)
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
                # Se ainda não tem cache após aguardar, continuar normalmente

            try:
                # Executar função original
                response = func(self, request, *args, **kwargs)

                # Cachear se sucesso
                if cache_key and response.status_code == 200:
                    cache.set(cache_key, response.data, ttl)

                return response
            finally:
                # Liberar lock
                if lock_acquired:
                    cache.delete(lock_key)
        return wrapper
    return decorator



def require_admin_access(message="Vendedores não têm permissão para acessar esta funcionalidade."):
    """Decorator para bloquear acesso de vendedores a funcionalidades administrativas.

    IMPORTANTE: Proprietário da loja (owner) SEMPRE tem acesso total, mesmo se vinculado como vendedor.
    Apenas vendedores comuns (não-owners) são bloqueados.

    Elimina código duplicado de verificação de permissão em múltiplos métodos.

    Args:
        message: Mensagem de erro personalizada (opcional)

    Usage:
        @require_admin_access('Vendedores não podem editar funcionários.')
        def update(self, request, *args, **kwargs):
            return super().update(request, *args, **kwargs)

    Returns:
        Decorator function que retorna 403 se usuário for vendedor (não-owner)

    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            from .utils import is_owner

            # Owner SEMPRE tem acesso total
            if is_owner(request):
                return func(self, request, *args, **kwargs)

            # Verificar se é vendedor comum (não-owner)
            if is_vendedor_usuario(request):
                return Response(
                    {"detail": message},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Executar função original
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
