#!/usr/bin/env python
"""
Script para testar otimizações de performance v1490
Mede hit rate do cache e número de queries
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.cache import cache
from django.db import connection, reset_queries
from django.conf import settings
from crm_vendas.models import Oportunidade, Lead, Atividade
from tenants.middleware import set_current_loja_id

# Habilitar query logging
settings.DEBUG = True

def test_cache_hit_rate():
    """Testa hit rate do cache"""
    print("\n=== TESTE 1: Hit Rate do Cache ===\n")
    
    loja_id = 172  # Felix Representações
    set_current_loja_id(loja_id)
    
    # Limpar cache de teste
    test_key = f'test_cache_hit_rate:{loja_id}'
    cache.delete(test_key)
    
    # Teste 1: Cache MISS
    result1 = cache.get(test_key)
    print(f"1. Cache GET (esperado MISS): {result1}")
    
    # Salvar no cache com TTL de 300s
    cache.set(test_key, {'data': 'test'}, 300)
    print(f"2. Cache SET com TTL=300s")
    
    # Teste 2: Cache HIT
    result2 = cache.get(test_key)
    print(f"3. Cache GET (esperado HIT): {result2}")
    
    # Verificar TTL
    ttl = cache.ttl(test_key)
    print(f"4. TTL restante: {ttl}s (de 300s)")
    
    if result2 and ttl > 290:
        print("\n✅ Cache funcionando corretamente com TTL de 300s")
    else:
        print("\n❌ Problema no cache")

def test_query_optimization():
    """Testa otimização de queries"""
    print("\n=== TESTE 2: Otimização de Queries ===\n")
    
    loja_id = 172
    set_current_loja_id(loja_id)
    
    # Resetar contador de queries
    reset_queries()
    
    # Buscar oportunidades com prefetch
    print("Buscando oportunidades com prefetch_related...")
    oportunidades = list(
        Oportunidade.objects
        .select_related('lead', 'vendedor', 'lead__conta')
        .prefetch_related(
            'atividades',
            'itens',
            'itens__produto_servico'
        )
        .filter(loja_id=loja_id)[:5]
    )
    
    # Acessar relacionamentos (não deve gerar queries adicionais)
    for oportunidade in oportunidades:
        _ = oportunidade.lead.nome
        _ = oportunidade.vendedor.nome if oportunidade.vendedor else None
        _ = list(oportunidade.itens.all())
        for item in oportunidade.itens.all():
            _ = item.produto_servico.nome if item.produto_servico else None
    
    num_queries = len(connection.queries)
    print(f"\nNúmero de queries executadas: {num_queries}")
    print(f"Oportunidades processadas: {len(oportunidades)}")
    
    if num_queries <= 5:
        print(f"\n✅ Otimização OK! Apenas {num_queries} queries para {len(oportunidades)} oportunidades")
    elif num_queries <= 10:
        print(f"\n⚠️ Otimização parcial. {num_queries} queries (esperado ≤5)")
    else:
        print(f"\n❌ Muitas queries! {num_queries} queries (esperado ≤5)")
    
    # Mostrar queries executadas
    print("\nQueries executadas:")
    for i, query in enumerate(connection.queries, 1):
        sql = query['sql'][:100]
        print(f"{i}. {sql}...")

def test_lead_optimization():
    """Testa otimização de queries de leads"""
    print("\n=== TESTE 3: Otimização de Leads ===\n")
    
    loja_id = 172
    set_current_loja_id(loja_id)
    
    reset_queries()
    
    # Buscar leads com prefetch
    print("Buscando leads com prefetch_related...")
    leads = list(
        Lead.objects
        .select_related('conta', 'vendedor')
        .prefetch_related(
            'oportunidades',
            'oportunidades__vendedor',
            'contatos'
        )
        .filter(loja_id=loja_id)[:5]
    )
    
    # Acessar relacionamentos
    for lead in leads:
        _ = lead.conta.nome if lead.conta else None
        _ = list(lead.oportunidades.all())
        _ = list(lead.contatos.all())
        for oportunidade in lead.oportunidades.all():
            _ = oportunidade.vendedor.nome if oportunidade.vendedor else None
    
    num_queries = len(connection.queries)
    print(f"\nNúmero de queries executadas: {num_queries}")
    print(f"Leads processados: {len(leads)}")
    
    if num_queries <= 4:
        print(f"\n✅ Otimização OK! Apenas {num_queries} queries para {len(leads)} leads")
    else:
        print(f"\n⚠️ {num_queries} queries (esperado ≤4)")

def test_redis_info():
    """Mostra informações do Redis"""
    print("\n=== TESTE 4: Informações do Redis ===\n")
    
    try:
        # Tentar obter estatísticas do Redis
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        info = redis_conn.info('stats')
        
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total > 0:
            hit_rate = (hits / total) * 100
            print(f"Keyspace Hits:   {hits:,}")
            print(f"Keyspace Misses: {misses:,}")
            print(f"Hit Rate:        {hit_rate:.2f}%")
            
            if hit_rate >= 75:
                print(f"\n✅ Hit rate excelente! ({hit_rate:.2f}%)")
            elif hit_rate >= 60:
                print(f"\n⚠️ Hit rate bom, mas pode melhorar ({hit_rate:.2f}%)")
            else:
                print(f"\n❌ Hit rate baixo ({hit_rate:.2f}%)")
        else:
            print("⚠️ Nenhuma estatística disponível ainda")
            
    except Exception as e:
        print(f"⚠️ Não foi possível obter estatísticas do Redis: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTE DE OTIMIZAÇÕES DE PERFORMANCE - v1490")
    print("=" * 60)
    
    try:
        test_cache_hit_rate()
        test_query_optimization()
        test_lead_optimization()
        test_redis_info()
        
        print("\n" + "=" * 60)
        print("✅ TESTES CONCLUÍDOS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro ao executar testes: {e}")
        import traceback
        traceback.print_exc()
