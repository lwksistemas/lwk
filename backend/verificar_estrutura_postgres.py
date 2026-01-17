#!/usr/bin/env python
"""
Script para verificar estrutura de tabelas no PostgreSQL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from django.db import connection

print("=" * 60)
print("VERIFICAÇÃO: ESTRUTURA POSTGRESQL")
print("=" * 60)

with connection.cursor() as cursor:
    # 1. Listar todos os schemas
    print("\n1. Schemas disponíveis:")
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
    """)
    schemas = cursor.fetchall()
    for schema in schemas:
        print(f"   - {schema[0]}")
    
    # 2. Verificar tabelas no schema public
    print("\n2. Tabelas no schema 'public':")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'suporte_%'
        ORDER BY table_name
    """)
    tables_public = cursor.fetchall()
    for table in tables_public:
        print(f"   - {table[0]}")
    
    # 3. Verificar tabelas no schema suporte
    print("\n3. Tabelas no schema 'suporte':")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'suporte'
        ORDER BY table_name
    """)
    tables_suporte = cursor.fetchall()
    for table in tables_suporte:
        print(f"   - {table[0]}")
    
    # 4. Verificar search_path atual
    print("\n4. Search path atual:")
    cursor.execute("SHOW search_path")
    search_path = cursor.fetchone()
    print(f"   {search_path[0]}")

print("\n" + "=" * 60)
print("✅ VERIFICAÇÃO CONCLUÍDA!")
print("=" * 60)
