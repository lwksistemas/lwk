#!/usr/bin/env python
"""
Script para verificar se a loja felix-5889 realmente existe no banco
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
    cursor = conn.cursor()
    
    print('='*60)
    print('VERIFICAÇÃO DA LOJA FELIX-5889')
    print('='*60)
    
    # 1. Verificar se loja existe na tabela superadmin_loja
    cursor.execute("""
        SELECT id, nome, slug, database_name, is_active, owner_id
        FROM superadmin_loja
        WHERE slug = 'felix-5889' OR id = 37
    """)
    loja = cursor.fetchone()
    
    if loja:
        print(f'\n❌ LOJA AINDA EXISTE NO BANCO!')
        print(f'  ID: {loja[0]}')
        print(f'  Nome: {loja[1]}')
        print(f'  Slug: {loja[2]}')
        print(f'  Database: {loja[3]}')
        print(f'  Ativa: {loja[4]}')
        print(f'  Owner ID: {loja[5]}')
    else:
        print(f'\n✅ Loja felix-5889 NÃO existe na tabela superadmin_loja')
    
    # 2. Verificar se schema existe
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name = 'loja_felix_5889'
    """)
    schema = cursor.fetchone()
    
    if schema:
        print(f'\n❌ SCHEMA AINDA EXISTE: {schema[0]}')
        
        # Contar tabelas no schema
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'loja_felix_5889' AND table_type = 'BASE TABLE'
        """)
        count = cursor.fetchone()[0]
        print(f'  Tabelas no schema: {count}')
    else:
        print(f'\n✅ Schema loja_felix_5889 NÃO existe')
    
    # 3. Verificar se owner existe
    if loja:
        owner_id = loja[5]
        cursor.execute("""
            SELECT id, username, email, is_active
            FROM auth_user
            WHERE id = %s
        """, [owner_id])
        owner = cursor.fetchone()
        
        if owner:
            print(f'\n❌ OWNER AINDA EXISTE:')
            print(f'  ID: {owner[0]}')
            print(f'  Username: {owner[1]}')
            print(f'  Email: {owner[2]}')
            print(f'  Ativo: {owner[3]}')
        else:
            print(f'\n✅ Owner (ID: {owner_id}) NÃO existe')
    
    # 4. Listar TODAS as lojas
    cursor.execute("""
        SELECT id, nome, slug, database_name
        FROM superadmin_loja
        ORDER BY id
    """)
    todas_lojas = cursor.fetchall()
    
    print(f'\n📊 TODAS AS LOJAS NO SISTEMA: {len(todas_lojas)}')
    for l in todas_lojas:
        print(f'  - ID:{l[0]:2d} | {l[2]:30s} | Schema: {l[3]}')
    
    print('\n' + '='*60)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
