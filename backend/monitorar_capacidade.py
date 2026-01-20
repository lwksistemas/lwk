#!/usr/bin/env python
"""
Script para monitorar capacidade atual do sistema
Mostra quantas lojas podem ser criadas com segurança
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.db import connection

def get_database_info():
    """Coleta informações do banco de dados"""
    with connection.cursor() as cursor:
        # 1. Contar schemas de lojas
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'loja_%'
        """)
        lojas_count = cursor.fetchone()[0]
        
        # 2. Contar total de tabelas
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        total_tables = cursor.fetchone()[0]
        
        # 3. Listar schemas de lojas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'loja_%'
            ORDER BY schema_name
        """)
        lojas_schemas = [row[0] for row in cursor.fetchall()]
        
        # 4. Tamanho do banco (aproximado)
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        db_size = cursor.fetchone()[0]
        
        return {
            'lojas_count': lojas_count,
            'total_tables': total_tables,
            'lojas_schemas': lojas_schemas,
            'db_size': db_size
        }

def calculate_capacity():
    """Calcula capacidade restante"""
    info = get_database_info()
    
    # Limites do PostgreSQL Essential-0
    MAX_TABLES = 4000
    MAX_STORAGE_MB = 1024  # 1 GB
    MAX_CONNECTIONS = 20
    
    # Estimativas
    TABLES_PER_LOJA = 18
    STORAGE_PER_LOJA_KB = 500  # Loja pequena
    
    # Cálculos
    used_tables = info['total_tables']
    available_tables = MAX_TABLES - used_tables
    max_lojas_by_tables = available_tables // TABLES_PER_LOJA
    
    # Estimativa de storage usado (baseado no número de lojas)
    estimated_storage_kb = info['lojas_count'] * STORAGE_PER_LOJA_KB
    available_storage_kb = (MAX_STORAGE_MB * 1024) - estimated_storage_kb
    max_lojas_by_storage = available_storage_kb // STORAGE_PER_LOJA_KB
    
    return {
        'current_lojas': info['lojas_count'],
        'used_tables': used_tables,
        'available_tables': available_tables,
        'max_lojas_by_tables': max_lojas_by_tables,
        'max_lojas_by_storage': max_lojas_by_storage,
        'db_size': info['db_size'],
        'lojas_schemas': info['lojas_schemas']
    }

def print_report():
    """Imprime relatório de capacidade"""
    capacity = calculate_capacity()
    
    print("=" * 70)
    print("📊 RELATÓRIO DE CAPACIDADE - LWK SISTEMAS")
    print("=" * 70)
    
    print(f"\n🏪 LOJAS ATUAIS:")
    print(f"   Lojas criadas: {capacity['current_lojas']}")
    print(f"   Schemas: {', '.join(capacity['lojas_schemas'][:5])}")
    if len(capacity['lojas_schemas']) > 5:
        print(f"            ... e mais {len(capacity['lojas_schemas']) - 5}")
    
    print(f"\n📊 USO DE RECURSOS:")
    print(f"   Tabelas usadas: {capacity['used_tables']:,}/4,000 ({capacity['used_tables']/40:.1f}%)")
    print(f"   Tamanho do banco: {capacity['db_size']}")
    
    print(f"\n🎯 CAPACIDADE RESTANTE:")
    print(f"   Por tabelas: {capacity['max_lojas_by_tables']} lojas")
    print(f"   Por storage: {capacity['max_lojas_by_storage']} lojas")
    
    # Determinar limitador principal
    limiting_factor = min(capacity['max_lojas_by_tables'], capacity['max_lojas_by_storage'])
    
    print(f"\n🚦 RECOMENDAÇÕES:")
    if limiting_factor > 50:
        status = "🟢 EXCELENTE"
        recommendation = "Sistema pode crescer tranquilamente"
    elif limiting_factor > 20:
        status = "🟡 ATENÇÃO"
        recommendation = "Monitorar crescimento, planejar upgrade"
    else:
        status = "🔴 CRÍTICO"
        recommendation = "Upgrade necessário em breve"
    
    print(f"   Status: {status}")
    print(f"   Lojas adicionais seguras: {limiting_factor}")
    print(f"   Recomendação: {recommendation}")
    
    print(f"\n💰 UPGRADE NECESSÁRIO QUANDO:")
    print(f"   - Mais de 80 lojas (recomendado)")
    print(f"   - Mais de 3,000 tabelas (75% do limite)")
    print(f"   - Tamanho > 700 MB (70% do limite)")
    print(f"   - Performance degradada")
    
    print(f"\n📈 PRÓXIMO PLANO:")
    print(f"   PostgreSQL Essential-1 ($50/mês)")
    print(f"   - 10 GB storage (10x mais)")
    print(f"   - 120 conexões (6x mais)")
    print(f"   - Capacidade: 500+ lojas")
    
    print("\n" + "=" * 70)
    print("✅ RELATÓRIO CONCLUÍDO!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        print_report()
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        print("Verifique se o banco de dados está acessível.")