#!/usr/bin/env python
"""
Script de Diagnóstico de Conexão PostgreSQL
Executa testes de conectividade e performance do banco de dados
"""
import os
import sys
import time
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.db.utils import OperationalError
from django.conf import settings


def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_database_config():
    """Testa configuração do banco de dados"""
    print_header("CONFIGURAÇÃO DO BANCO DE DADOS")
    
    db_config = settings.DATABASES['default']
    
    print(f"Engine: {db_config.get('ENGINE')}")
    print(f"Name: {db_config.get('NAME', 'N/A')}")
    print(f"Host: {db_config.get('HOST', 'N/A')}")
    print(f"Port: {db_config.get('PORT', 'N/A')}")
    print(f"User: {db_config.get('USER', 'N/A')}")
    print(f"CONN_MAX_AGE: {db_config.get('CONN_MAX_AGE', 'N/A')}")
    print(f"CONN_HEALTH_CHECKS: {db_config.get('CONN_HEALTH_CHECKS', 'N/A')}")
    
    options = db_config.get('OPTIONS', {})
    if options:
        print("\nOPTIONS:")
        for key, value in options.items():
            print(f"  {key}: {value}")
    
    # Verificar DATABASE_URL
    database_url = os.environ.get('DATABASE_URL', 'Não configurada')
    if database_url != 'Não configurada':
        # Ocultar senha
        import re
        database_url_safe = re.sub(r':([^:@]+)@', ':***@', database_url)
        print(f"\nDATABASE_URL: {database_url_safe}")
    else:
        print(f"\nDATABASE_URL: {database_url}")


def test_connection():
    """Testa conexão básica com o banco"""
    print_header("TESTE DE CONEXÃO")
    
    try:
        start_time = time.time()
        connection.ensure_connection()
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Conexão estabelecida com sucesso!")
        print(f"⏱️  Tempo: {elapsed:.2f}ms")
        
        return True
        
    except OperationalError as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def test_query_performance():
    """Testa performance de queries"""
    print_header("TESTE DE PERFORMANCE")
    
    try:
        # Query simples
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Query SELECT 1: {elapsed:.2f}ms")
        
        # Query de versão
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Query version(): {elapsed:.2f}ms")
        print(f"📊 Versão: {version}")
        
        # Query de contagem de conexões
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            connections = cursor.fetchone()[0]
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Query conexões ativas: {elapsed:.2f}ms")
        print(f"🔌 Conexões ativas: {connections}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar queries: {e}")
        return False


def test_connection_retry():
    """Testa retry de conexão"""
    print_header("TESTE DE RETRY")
    
    max_retries = 3
    success_count = 0
    total_time = 0
    
    for i in range(max_retries):
        try:
            # Fechar conexão anterior
            connection.close()
            
            # Tentar conectar
            start_time = time.time()
            connection.ensure_connection()
            elapsed = (time.time() - start_time) * 1000
            
            print(f"✅ Tentativa {i+1}: {elapsed:.2f}ms")
            success_count += 1
            total_time += elapsed
            
        except Exception as e:
            print(f"❌ Tentativa {i+1}: {e}")
    
    if success_count > 0:
        avg_time = total_time / success_count
        print(f"\n📊 Taxa de sucesso: {success_count}/{max_retries} ({success_count/max_retries*100:.1f}%)")
        print(f"⏱️  Tempo médio: {avg_time:.2f}ms")
        return True
    else:
        print(f"\n❌ Todas as tentativas falharam")
        return False


def test_timeout():
    """Testa comportamento de timeout"""
    print_header("TESTE DE TIMEOUT")
    
    try:
        # Query que demora (pg_sleep)
        print("Executando query com pg_sleep(2)...")
        start_time = time.time()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_sleep(2)")
        
        elapsed = (time.time() - start_time) * 1000
        print(f"✅ Query completada: {elapsed:.2f}ms")
        
        return True
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"❌ Timeout após {elapsed:.2f}ms: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "🔍 DIAGNÓSTICO DE CONEXÃO POSTGRESQL" + "\n")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'config': True,
        'connection': False,
        'performance': False,
        'retry': False,
        'timeout': False,
    }
    
    # Teste 1: Configuração
    test_database_config()
    
    # Teste 2: Conexão
    results['connection'] = test_connection()
    
    if results['connection']:
        # Teste 3: Performance
        results['performance'] = test_query_performance()
        
        # Teste 4: Retry
        results['retry'] = test_connection_retry()
        
        # Teste 5: Timeout
        results['timeout'] = test_timeout()
    
    # Resumo
    print_header("RESUMO")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"\nTestes executados: {total_tests}")
    print(f"Testes aprovados: {passed_tests}")
    print(f"Taxa de sucesso: {passed_tests/total_tests*100:.1f}%")
    
    print("\nDetalhes:")
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name.upper()}: {status}")
    
    # Recomendações
    print_header("RECOMENDAÇÕES")
    
    if not results['connection']:
        print("❌ CRÍTICO: Não foi possível conectar ao banco de dados")
        print("\nVerifique:")
        print("  1. DATABASE_URL está configurada corretamente")
        print("  2. PostgreSQL está acessível (firewall/security groups)")
        print("  3. Credenciais estão corretas")
        print("  4. Banco de dados está rodando")
        print("\nComandos úteis:")
        print("  heroku config:get DATABASE_URL --app lwksistemas")
        print("  heroku pg:info --app lwksistemas")
        print("  heroku pg:psql --app lwksistemas -c 'SELECT 1;'")
    
    elif not results['performance']:
        print("⚠️ ATENÇÃO: Conexão OK mas queries estão falhando")
        print("\nVerifique:")
        print("  1. Permissões do usuário no banco")
        print("  2. Queries estão corretas")
        print("  3. Tabelas existem")
    
    elif not results['retry']:
        print("⚠️ ATENÇÃO: Retry de conexão está falhando")
        print("\nVerifique:")
        print("  1. CONN_MAX_AGE está configurado corretamente")
        print("  2. Connection pooling está funcionando")
    
    elif not results['timeout']:
        print("⚠️ ATENÇÃO: Timeout de queries está muito baixo")
        print("\nVerifique:")
        print("  1. statement_timeout está configurado corretamente")
        print("  2. Queries não estão demorando muito")
    
    else:
        print("✅ Todos os testes passaram!")
        print("\nSistema está funcionando corretamente.")
    
    print("\n" + "=" * 60 + "\n")
    
    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
