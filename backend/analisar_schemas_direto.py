#!/usr/bin/env python
"""
Script para analisar schemas PostgreSQL diretamente (sem Django completo)
"""
import os
import psycopg2
from urllib.parse import urlparse

# Obter DATABASE_URL do ambiente
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada no ambiente")
    print("Execute: export DATABASE_URL='sua_url_do_postgres'")
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
        database=url.path[1:]  # Remove a barra inicial
    )
    cursor = conn.cursor()
    
    print('='*60)
    print('ANÁLISE DE SCHEMAS E LOJAS')
    print('='*60)
    
    # 1. Listar todos os schemas no PostgreSQL
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'loja_%' 
        ORDER BY schema_name
    """)
    schemas_db = [r[0] for r in cursor.fetchall()]
    
    print(f'\n📊 Schemas no PostgreSQL: {len(schemas_db)}')
    for s in schemas_db:
        print(f'  - {s}')
    
    # 2. Listar todas as lojas no Django (tabela superadmin_loja)
    cursor.execute("""
        SELECT id, nome, slug, database_name, database_created, is_active
        FROM superadmin_loja
        ORDER BY id
    """)
    lojas_list = cursor.fetchall()
    
    print(f'\n📊 Lojas no Django: {len(lojas_list)}')
    for loja in lojas_list:
        loja_id, nome, slug, database_name, database_created, is_active = loja
        schema = database_name.replace('-', '_')
        status = '✅' if is_active else '❌'
        db_created = '✅' if database_created else '❌'
        print(f'  {status} ID:{loja_id:2d} | {slug:30s} | DB:{db_created} | Schema: {schema}')
    
    # 3. Identificar schemas órfãos (no DB mas sem loja)
    schemas_esperados = [loja[3].replace('-', '_') for loja in lojas_list]  # database_name
    schemas_orfaos = [s for s in schemas_db if s not in schemas_esperados]
    
    print(f'\n⚠️  Schemas ÓRFÃOS (no DB mas sem loja): {len(schemas_orfaos)}')
    for s in schemas_orfaos:
        print(f'  - {s}')
    
    # 4. Identificar lojas sem schema (loja existe mas schema não)
    lojas_sem_schema = []
    for loja in lojas_list:
        loja_id, nome, slug, database_name, database_created, is_active = loja
        schema = database_name.replace('-', '_')
        if schema not in schemas_db:
            lojas_sem_schema.append(loja)
    
    print(f'\n⚠️  Lojas SEM SCHEMA (loja existe mas schema não): {len(lojas_sem_schema)}')
    for loja in lojas_sem_schema:
        loja_id, nome, slug, database_name, database_created, is_active = loja
        schema = database_name.replace('-', '_')
        print(f'  - ID:{loja_id} | {slug} | Schema esperado: {schema}')
    
    # 5. Verificar schemas vazios (sem tabelas)
    print(f'\n📊 Verificando tabelas em cada schema...')
    schemas_vazios = []
    schemas_com_tabelas = {}
    
    for schema in schemas_db:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
        """, [schema])
        count = cursor.fetchone()[0]
        
        schemas_com_tabelas[schema] = count
        
        if count == 0:
            schemas_vazios.append(schema)
            print(f'  ⚠️  {schema}: 0 tabelas (VAZIO)')
        else:
            print(f'  ✅ {schema}: {count} tabelas')
    
    print(f'\n⚠️  Schemas VAZIOS (sem tabelas): {len(schemas_vazios)}')
    for s in schemas_vazios:
        print(f'  - {s}')
    
    # 6. Resumo
    print(f'\n{"="*60}')
    print('RESUMO DA ANÁLISE')
    print('='*60)
    print(f'Total de schemas no PostgreSQL: {len(schemas_db)}')
    print(f'Total de lojas no Django: {len(lojas_list)}')
    print(f'⚠️  Schemas órfãos (sem loja): {len(schemas_orfaos)}')
    print(f'⚠️  Lojas sem schema: {len(lojas_sem_schema)}')
    print(f'⚠️  Schemas vazios (sem tabelas): {len(schemas_vazios)}')
    print('='*60)
    
    # 7. Recomendações
    if schemas_orfaos or lojas_sem_schema or schemas_vazios:
        print(f'\n{"="*60}')
        print('RECOMENDAÇÕES')
        print('='*60)
        
        if schemas_orfaos:
            print(f'\n⚠️  {len(schemas_orfaos)} schema(s) órfão(s) encontrado(s)')
            print('Ação recomendada: Excluir schemas órfãos para liberar espaço')
            print('\nComandos SQL para excluir:')
            for s in schemas_orfaos:
                print(f'  DROP SCHEMA IF EXISTS "{s}" CASCADE;')
        
        if lojas_sem_schema:
            print(f'\n⚠️  {len(lojas_sem_schema)} loja(s) sem schema encontrada(s)')
            print('Ação recomendada: Excluir lojas inválidas')
            print('\nLojas para excluir:')
            for loja in lojas_sem_schema:
                loja_id, nome, slug, database_name, database_created, is_active = loja
                print(f'  - ID:{loja_id} | {slug}')
        
        if schemas_vazios:
            print(f'\n⚠️  {len(schemas_vazios)} schema(s) vazio(s) encontrado(s)')
            print('Ação recomendada: Aplicar migrations ou excluir schemas vazios')
            print('\nSchemas vazios:')
            for s in schemas_vazios:
                # Encontrar loja correspondente
                loja_correspondente = None
                for loja in lojas_list:
                    loja_id, nome, slug, database_name, database_created, is_active = loja
                    if database_name.replace('-', '_') == s:
                        loja_correspondente = loja
                        break
                
                if loja_correspondente:
                    loja_id, nome, slug, database_name, database_created, is_active = loja_correspondente
                    print(f'  - {s} (Loja ID:{loja_id} | {slug})')
                else:
                    print(f'  - {s} (órfão)')
    else:
        print(f'\n{"="*60}')
        print('✅ SISTEMA OK - Nenhum problema encontrado!')
        print('='*60)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
    exit(1)
