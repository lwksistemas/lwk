"""
Serviço de Cache para Estatísticas de Auditoria

Implementa cache Redis para melhorar performance de queries pesadas.
TTL padrão: 5 minutos (300 segundos)
"""

import logging
import json
from typing import Any, Optional, Callable
from functools import wraps
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Serviço para gerenciar cache de estatísticas.
    
    Usa Django cache framework (configurado para Redis em produção).
    """
    
    # TTL padrão: 5 minutos
    DEFAULT_TTL = 300
    
    # Prefixo para chaves de cache
    PREFIX = 'superadmin:stats:'
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        Obtém valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não existir
        """
        full_key = f"{cls.PREFIX}{key}"
        try:
            value = cache.get(full_key)
            if value is not None:
                logger.debug(f"Cache HIT: {full_key}")
            else:
                logger.debug(f"Cache MISS: {full_key}")
            return value
        except Exception as e:
            logger.error(f"Erro ao obter cache {full_key}: {e}")
            return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos (padrão: 5 minutos)
            
        Returns:
            True se armazenado com sucesso
        """
        full_key = f"{cls.PREFIX}{key}"
        ttl = ttl or cls.DEFAULT_TTL
        
        try:
            cache.set(full_key, value, ttl)
            logger.debug(f"Cache SET: {full_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar cache {full_key}: {e}")
            return False
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        Remove valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido com sucesso
        """
        full_key = f"{cls.PREFIX}{key}"
        try:
            cache.delete(full_key)
            logger.debug(f"Cache DELETE: {full_key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache {full_key}: {e}")
            return False
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """
        Remove todas as chaves que correspondem ao padrão.
        
        Args:
            pattern: Padrão de busca (ex: 'acoes_por_dia:*')
            
        Returns:
            Número de chaves removidas
        """
        full_pattern = f"{cls.PREFIX}{pattern}"
        try:
            # Obter todas as chaves que correspondem ao padrão
            keys = cache.keys(full_pattern)
            if keys:
                cache.delete_many(keys)
                logger.info(f"Cache DELETE_PATTERN: {full_pattern} ({len(keys)} chaves)")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao deletar padrão {full_pattern}: {e}")
            return 0
    
    @classmethod
    def clear_all(cls) -> bool:
        """
        Limpa todo o cache de estatísticas.
        
        Returns:
            True se limpo com sucesso
        """
        try:
            deleted = cls.delete_pattern('*')
            logger.info(f"Cache CLEAR_ALL: {deleted} chaves removidas")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    @classmethod
    def get_or_set(cls, key: str, callback: Callable, ttl: Optional[int] = None) -> Any:
        """
        Obtém valor do cache ou executa callback e armazena resultado.
        
        Args:
            key: Chave do cache
            callback: Função a executar se cache não existir
            ttl: Tempo de vida em segundos
            
        Returns:
            Valor do cache ou resultado do callback
        """
        # Tentar obter do cache
        value = cls.get(key)
        
        if value is not None:
            return value
        
        # Executar callback
        try:
            value = callback()
            cls.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Erro ao executar callback para {key}: {e}")
            raise


def cached_stat(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator para cachear resultados de métodos de estatísticas.
    
    Args:
        ttl: Tempo de vida em segundos (padrão: 5 minutos)
        key_prefix: Prefixo adicional para a chave (padrão: nome da função)
    
    Exemplo:
        @cached_stat(ttl=600, key_prefix='acoes_por_dia')
        def acoes_por_dia(self, request):
            # ... lógica pesada ...
            return Response(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Construir chave do cache
            prefix = key_prefix or func.__name__
            
            # Incluir parâmetros da request na chave
            cache_key_parts = [prefix]
            
            # Se houver request, incluir query params
            if len(args) > 1 and hasattr(args[1], 'query_params'):
                request = args[1]
                params = dict(request.query_params)
                # Ordenar para garantir consistência
                params_str = json.dumps(params, sort_keys=True)
                cache_key_parts.append(params_str)
            
            cache_key = ':'.join(cache_key_parts)
            
            # Tentar obter do cache
            cached_data = CacheService.get(cache_key)
            if cached_data is not None:
                logger.info(f"Retornando estatística do cache: {prefix}")
                # Importar Response aqui para evitar circular import
                from rest_framework.response import Response
                return Response(cached_data)
            
            # Executar função
            logger.info(f"Calculando estatística: {prefix}")
            result = func(*args, **kwargs)
            
            # Armazenar no cache (apenas os dados, não o objeto Response)
            if hasattr(result, 'data'):
                try:
                    CacheService.set(cache_key, result.data, ttl)
                except Exception as e:
                    logger.error(f"Erro ao armazenar cache {cache_key}: {e}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_stats_cache():
    """
    Invalida todo o cache de estatísticas.
    
    Deve ser chamado quando:
    - Novos logs são criados
    - Violações são resolvidas
    - Dados são modificados
    """
    logger.info("Invalidando cache de estatísticas...")
    CacheService.clear_all()
