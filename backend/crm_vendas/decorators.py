"""
Decorators reutilizáveis para CRM Vendas.
Elimina código duplicado de cache em list() e bloqueio de vendedor.
"""
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from .cache import CRMCacheManager
from .utils import get_current_vendedor_id, is_vendedor_usuario
from tenants.middleware import get_current_loja_id


def cache_list_response(cache_prefix, ttl=120, extra_keys=None):
    """
    Decorator para cachear resposta de list().
    
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
            loja_id = get_current_loja_id()
            vendedor_id = get_current_vendedor_id(request)
            
            # Construir kwargs para chave de cache
            cache_kwargs = {}
            if extra_keys:
                for key in extra_keys:
                    value = request.query_params.get(key)
                    if value:
                        cache_kwargs[key] = value
            
            # Para atividades, incluir versão na chave
            if cache_prefix == CRMCacheManager.ATIVIDADES:
                version_key = CRMCacheManager.get_cache_key(
                    CRMCacheManager.ATIVIDADES_VERSION,
                    loja_id
                )
                version = cache.get(version_key, 0)
                cache_kwargs['v'] = version
            
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



def require_admin_access(message='Vendedores não têm permissão para acessar esta funcionalidade.'):
    """
    Decorator para bloquear acesso de vendedores a funcionalidades administrativas.
    
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
            # Verificar se é proprietário da loja
            loja_id = get_current_loja_id()
            if loja_id:
                from superadmin.models import Loja
                try:
                    loja = Loja.objects.using('default').filter(id=loja_id).first()
                    if loja and loja.owner_id == request.user.id:
                        # Owner SEMPRE tem acesso total
                        return func(self, request, *args, **kwargs)
                except Exception:
                    pass
            
            # Verificar se é vendedor comum (não-owner)
            if is_vendedor_usuario(request):
                return Response(
                    {'detail': message},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Executar função original
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def invalidate_cache_on_change(*cache_types):
    """
    Decorator para invalidar cache automaticamente após operações de escrita.
    
    Elimina código duplicado de invalidação de cache em perform_create/update/destroy.
    
    Args:
        *cache_types: Tipos de cache para invalidar (ex: 'contas', 'atividades', 'dashboard')
    
    Usage:
        @invalidate_cache_on_change('contas', 'dashboard')
        def perform_create(self, serializer):
            serializer.save()
    
    Returns:
        Decorator function que invalida cache após execução
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Executar função original
            result = func(self, *args, **kwargs)
            
            # Invalidar caches especificados
            loja_id = get_current_loja_id()
            if loja_id:
                for cache_type in cache_types:
                    if cache_type == 'contas':
                        CRMCacheManager.invalidate_contas(loja_id)
                    elif cache_type == 'leads':
                        CRMCacheManager.invalidate_leads(loja_id)
                    elif cache_type == 'contatos':
                        CRMCacheManager.invalidate_contatos(loja_id)
                    elif cache_type == 'oportunidades':
                        CRMCacheManager.invalidate_oportunidades(loja_id)
                    elif cache_type == 'atividades':
                        CRMCacheManager.invalidate_atividades(loja_id)
                    elif cache_type == 'dashboard':
                        CRMCacheManager.invalidate_dashboard(loja_id)
            
            return result
        return wrapper
    return decorator
