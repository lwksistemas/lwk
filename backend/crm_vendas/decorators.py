"""
Decorators reutilizáveis para CRM Vendas.
Elimina código duplicado de cache em list().
"""
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from .cache import CRMCacheManager
from .utils import get_current_vendedor_id
from tenants.middleware import get_current_loja_id


def cache_list_response(cache_prefix, ttl=120, extra_keys=None):
    """
    Decorator para cachear resposta de list().
    
    Gera chave de cache baseada em:
    - loja_id
    - vendedor_id (ou 'owner')
    - query params especificados em extra_keys
    
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
            loja_id = get_current_loja_id()
            vendedor_id = get_current_vendedor_id(request)
            
            # Construir kwargs para chave de cache
            cache_kwargs = {}
            if extra_keys:
                for key in extra_keys:
                    value = request.query_params.get(key)
                    if value:
                        cache_kwargs[key] = value
            
            # Gerar chave de cache
            cache_key = CRMCacheManager.get_cache_key(
                cache_prefix,
                loja_id,
                vendedor_id,
                **cache_kwargs
            )
            
            # Tentar obter do cache
            if cache_key:
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
            
            # Executar função original
            response = func(self, request, *args, **kwargs)
            
            # Cachear se sucesso
            if cache_key and response.status_code == 200:
                cache.set(cache_key, response.data, ttl)
            
            return response
        return wrapper
    return decorator
