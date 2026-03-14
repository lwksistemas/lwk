#!/usr/bin/env python
"""
Script para limpar schemas órfãos do PostgreSQL
"""
import os
import psycopg2
from urllib.parse import urlparse

# Obter DATABASE_URL do ambiente
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada no ambiente")
    exit(1)

# Parse da URL
url = urlparse(DATABASE_URL)

# Conectar ao PostgreSQL
try:
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        database=url.path[1:]
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print('='*60)
    print('LIMPEZA DE SCHEMAS ÓRFÃOS')
    print('='*60)
    
    # 1. Listar schemas no PostgreSQL
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'loja_%' 
        ORDER BY schema_name
    """)
    schemas_db = [r[0] for r in cursor.fetchall()]
    
    print(f'\n📊 Schemas encontrados: {len(schemas_db)}')
    for s in schemas_db:
        print(f'  - {s}')
    
    # 2. Listar lojas no Django
    cursor.execute("""
        SELECT id, database_name
        FROM superadmin_loja
        ORDER BY id
    """)
    lojas_list = cursor.fetchall()
    
    print(f'\n📊 Lojas no Django: {len(lojas_list)}')
    
    # 3. Identificar schemas órfãos
    schemas_esperados = [loja[1].replace('-', '_') for loja in lojas_list]
    schemas_orfaos = [s for s in schemas_db if s not in schemas_esperados]
    
    print(f'\n⚠️  Schemas órfãos encontrados: {len(schemas_orfaos)}')
    
    if not schemas_orfaos:
        print('✅ Nenhum schema órfão encontrado!')
        cursor.close()
        conn.close()
        exit(0)
    
    # 4. Excluir schemas órfãos
    print('\n🗑️  Excluindo schemas órfãos...')
    for schema in schemas_orfaos:
        try:
            print(f'  Excluindo schema: {schema}')
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            print(f'  ✅ Schema {schema} excluído')
        except Exception as e:
            print(f'  ❌ Erro ao excluir {schema}: {e}')
    
    print('\n✅ Limpeza concluída!')
    
    # 5. Verificar resultado
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'loja_%' 
        ORDER BY schema_name
    """)
    schemas_restantes = [r[0] for r in cursor.fetchall()]
    
    print(f'\n📊 Schemas restantes: {len(schemas_restantes)}')
    for s in schemas_restantes:
        print(f'  - {s}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
