"""
Testes para o CacheService

Testa funcionalidades de cache Redis/LocMemCache.
"""

import pytest
from django.core.cache import cache
from superadmin.cache import CacheService, cached_stat
from rest_framework.response import Response


@pytest.fixture(autouse=True)
def clear_cache():
    """Limpa cache antes de cada teste"""
    cache.clear()
    CacheService._ultimas_notificacoes = {}
    yield
    cache.clear()


@pytest.mark.django_db
class TestCacheService:
    """Testes para CacheService"""
    
    def test_set_and_get(self):
        """Testa armazenar e recuperar valor"""
        key = 'test_key'
        value = {'data': 'test_value'}
        
        # Armazenar
        result = CacheService.set(key, value, ttl=60)
        assert result is True
        
        # Recuperar
        cached_value = CacheService.get(key)
        assert cached_value == value
    
    def test_get_nonexistent(self):
        """Testa recuperar valor inexistente"""
        value = CacheService.get('nonexistent_key')
        assert value is None
    
    def test_delete(self):
        """Testa deletar valor"""
        key = 'test_key'
        value = 'test_value'
        
        # Armazenar
        CacheService.set(key, value)
        assert CacheService.get(key) == value
        
        # Deletar
        result = CacheService.delete(key)
        assert result is True
        assert CacheService.get(key) is None
    
    def test_clear_all(self):
        """Testa limpar todo o cache"""
        # Armazenar múltiplos valores
        CacheService.set('key1', 'value1')
        CacheService.set('key2', 'value2')
        CacheService.set('key3', 'value3')
        
        # Limpar tudo
        result = CacheService.clear_all()
        assert result is True
        
        # Verificar que foram removidos
        assert CacheService.get('key1') is None
        assert CacheService.get('key2') is None
        assert CacheService.get('key3') is None
    
    def test_get_or_set_cache_miss(self):
        """Testa get_or_set com cache miss"""
        key = 'test_key'
        expected_value = 'computed_value'
        
        # Callback que será executado
        def callback():
            return expected_value
        
        # Primeira chamada (cache miss)
        value = CacheService.get_or_set(key, callback, ttl=60)
        assert value == expected_value
        
        # Verificar que foi armazenado
        cached_value = CacheService.get(key)
        assert cached_value == expected_value
    
    def test_get_or_set_cache_hit(self):
        """Testa get_or_set com cache hit"""
        key = 'test_key'
        cached_value = 'cached_value'
        
        # Armazenar valor no cache
        CacheService.set(key, cached_value)
        
        # Callback que NÃO deve ser executado
        callback_executed = False
        def callback():
            nonlocal callback_executed
            callback_executed = True
            return 'new_value'
        
        # Chamada (cache hit)
        value = CacheService.get_or_set(key, callback)
        assert value == cached_value
        assert callback_executed is False  # Callback não foi executado
    
    def test_ttl_expiration(self):
        """Testa expiração de TTL"""
        import time
        
        key = 'test_key'
        value = 'test_value'
        
        # Armazenar com TTL de 1 segundo
        CacheService.set(key, value, ttl=1)
        
        # Verificar que está no cache
        assert CacheService.get(key) == value
        
        # Aguardar expiração
        time.sleep(2)
        
        # Verificar que expirou
        assert CacheService.get(key) is None
    
    def test_prefix_isolation(self):
        """Testa isolamento de prefixo"""
        key = 'test_key'
        value = 'test_value'
        
        # Armazenar via CacheService (com prefixo)
        CacheService.set(key, value)
        
        # Tentar recuperar diretamente do cache (sem prefixo)
        direct_value = cache.get(key)
        assert direct_value is None  # Não encontra sem prefixo
        
        # Recuperar via CacheService (com prefixo)
        cached_value = CacheService.get(key)
        assert cached_value == value


@pytest.mark.django_db
class TestCachedStatDecorator:
    """Testes para decorator @cached_stat"""
    
    def test_decorator_cache_miss(self):
        """Testa decorator com cache miss"""
        call_count = 0
        
        @cached_stat(ttl=60, key_prefix='test_stat')
        def expensive_function(request):
            nonlocal call_count
            call_count += 1
            return Response({'result': 'computed'})
        
        # Mock request
        class MockRequest:
            query_params = {}
        
        request = MockRequest()
        
        # Primeira chamada (cache miss)
        response1 = expensive_function(None, request)
        assert call_count == 1
        assert response1.data == {'result': 'computed'}
        
        # Segunda chamada (cache hit)
        response2 = expensive_function(None, request)
        assert call_count == 1  # Não executou novamente
        assert response2.data == {'result': 'computed'}
    
    def test_decorator_with_params(self):
        """Testa decorator com parâmetros diferentes"""
        call_count = 0
        
        @cached_stat(ttl=60, key_prefix='test_stat')
        def function_with_params(request):
            nonlocal call_count
            call_count += 1
            dias = request.query_params.get('dias', '30')
            return Response({'dias': dias})
        
        # Mock requests com parâmetros diferentes
        class MockRequest:
            def __init__(self, params):
                self.query_params = params
        
        request1 = MockRequest({'dias': '7'})
        request2 = MockRequest({'dias': '30'})
        
        # Primeira chamada (dias=7)
        response1 = function_with_params(None, request1)
        assert call_count == 1
        assert response1.data == {'dias': '7'}
        
        # Segunda chamada (dias=30) - cache miss (parâmetros diferentes)
        response2 = function_with_params(None, request2)
        assert call_count == 2
        assert response2.data == {'dias': '30'}
        
        # Terceira chamada (dias=7) - cache hit
        response3 = function_with_params(None, request1)
        assert call_count == 2  # Não executou novamente
        assert response3.data == {'dias': '7'}
    
    def test_decorator_custom_ttl(self):
        """Testa decorator com TTL customizado"""
        import time
        
        @cached_stat(ttl=1, key_prefix='test_stat')
        def function_with_ttl(request):
            return Response({'timestamp': time.time()})
        
        class MockRequest:
            query_params = {}
        
        request = MockRequest()
        
        # Primeira chamada
        response1 = function_with_ttl(None, request)
        timestamp1 = response1.data['timestamp']
        
        # Segunda chamada imediata (cache hit)
        response2 = function_with_ttl(None, request)
        timestamp2 = response2.data['timestamp']
        assert timestamp1 == timestamp2
        
        # Aguardar expiração
        time.sleep(2)
        
        # Terceira chamada (cache miss após expiração)
        response3 = function_with_ttl(None, request)
        timestamp3 = response3.data['timestamp']
        assert timestamp3 > timestamp1


@pytest.mark.django_db
class TestCacheIntegration:
    """Testes de integração do cache"""
    
    def test_cache_performance(self):
        """Testa melhoria de performance com cache"""
        import time
        
        @cached_stat(ttl=60, key_prefix='perf_test')
        def slow_function(request):
            time.sleep(0.1)  # Simular query pesada
            return Response({'result': 'data'})
        
        class MockRequest:
            query_params = {}
        
        request = MockRequest()
        
        # Primeira chamada (sem cache)
        start1 = time.time()
        slow_function(None, request)
        duration1 = time.time() - start1
        assert duration1 >= 0.1
        
        # Segunda chamada (com cache)
        start2 = time.time()
        slow_function(None, request)
        duration2 = time.time() - start2
        assert duration2 < 0.05  # Muito mais rápido
        
        # Verificar melhoria
        improvement = duration1 / duration2
        assert improvement > 2  # Pelo menos 2x mais rápido
