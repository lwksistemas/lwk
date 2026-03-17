#!/usr/bin/env python
"""
Análise completa de órfãos no sistema
Identifica: lojas, schemas, usuários, financeiros órfãos
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from superadmin.models import Loja, FinanceiroLoja


def analisar_orfaos():
    print("\n" + "="*80)
    print("ANÁLISE COMPLETA DE ÓRFÃOS NO SISTEMA")
    print("="*80 + "\n")
    
    # 1. Schemas PostgreSQL órfãos
    print("1. SCHEMAS POSTGRESQL ÓRFÃOS")
    print("-" * 80)
    
    with connection.cursor() as cursor:
        # Buscar todos os schemas que começam com 'loja_'
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'loja_%'
            ORDER BY schema_name;
        """)
        schemas_db = [row[0] for row in cursor.fetchall()]
    
    # Buscar database_names das lojas
    lojas = Loja.objects.all()
    schemas_lojas = [loja.database_name.replace('-', '_') for loja in lojas]
    
    schemas_orfaos = [s for s in schemas_db if s not in schemas_lojas]
    
    print(f"Total de schemas no PostgreSQL: {len(schemas_db)}")
    print(f"Total de lojas no sistema: {len(schemas_lojas)}")
    print(f"Schemas órfãos: {len(schemas_orfaos)}")
    
    if schemas_orfaos:
        print("\n⚠️  SCHEMAS ÓRFÃOS ENCONTRADOS:")
        for schema in schemas_orfaos:
            # Contar tabelas no schema
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE';
                """, [schema])
                tabelas_count = cursor.fetchone()[0]
            
            print(f"   - {schema} ({tabelas_count} tabelas)")
    else:
        print("✅ Nenhum schema órfão encontrado")
    
    print()
    
    # 2. Lojas com schemas vazios
    print("2. LOJAS COM SCHEMAS VAZIOS")
    print("-" * 80)
    
    lojas_vazias = []
    for loja in lojas:
        schema_name = loja.database_name.replace('-', '_')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'django_%%';
            """, [schema_name])
            tabelas_count = cursor.fetchone()[0]
        
        if tabelas_count == 0:
            lojas_vazias.append((loja.id, loja.slug, loja.nome, schema_name))
    
    print(f"Lojas com schemas vazios: {len(lojas_vazias)}")
    
    if lojas_vazias:
        print("\n⚠️  LOJAS COM SCHEMAS VAZIOS:")
        for loja_id, slug, nome, schema in lojas_vazias:
            print(f"   - ID: {loja_id}, Slug: {slug}, Nome: {nome}, Schema: {schema}")
    else:
        print("✅ Todas as lojas têm schemas com tabelas")
    
    print()
    
    # 3. Usuários órfãos
    print("3. USUÁRIOS ÓRFÃOS (sem lojas)")
    print("-" * 80)
    
    usuarios_orfaos = []
    for user in User.objects.filter(is_superuser=False, is_staff=False):
        if not user.lojas_owned.exists():
            usuarios_orfaos.append((user.id, user.username, user.email))
    
    print(f"Usuários órfãos: {len(usuarios_orfaos)}")
    
    if usuarios_orfaos:
        print("\n⚠️  USUÁRIOS ÓRFÃOS:")
        for user_id, username, email in usuarios_orfaos:
            print(f"   - ID: {user_id}, Username: {username}, Email: {email}")
    else:
        print("✅ Nenhum usuário órfão encontrado")
    
    print()
    
    # 4. FinanceiroLoja órfãos
    print("4. FINANCEIRO ÓRFÃO (sem loja)")
    print("-" * 80)
    
    financeiros_orfaos = []
    for financeiro in FinanceiroLoja.objects.all():
        if not Loja.objects.filter(id=financeiro.loja_id).exists():
            financeiros_orfaos.append((financeiro.id, financeiro.loja_id))
    
    print(f"Financeiros órfãos: {len(financeiros_orfaos)}")
    
    if financeiros_orfaos:
        print("\n⚠️  FINANCEIROS ÓRFÃOS:")
        for fin_id, loja_id in financeiros_orfaos:
            print(f"   - Financeiro ID: {fin_id}, Loja ID: {loja_id} (loja não existe)")
    else:
        print("✅ Nenhum financeiro órfão encontrado")
    
    print()
    
    # 5. Resumo
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"Schemas órfãos: {len(schemas_orfaos)}")
    print(f"Lojas com schemas vazios: {len(lojas_vazias)}")
    print(f"Usuários órfãos: {len(usuarios_orfaos)}")
    print(f"Financeiros órfãos: {len(financeiros_orfaos)}")
    print()
    
    total_orfaos = len(schemas_orfaos) + len(lojas_vazias) + len(usuarios_orfaos) + len(financeiros_orfaos)
    
    if total_orfaos > 0:
        print(f"⚠️  TOTAL DE ÓRFÃOS: {total_orfaos}")
        print("\nExecute o script de limpeza para remover os órfãos.")
    else:
        print("✅ SISTEMA LIMPO - Nenhum órfão encontrado!")
    
    print()
    
    return {
        'schemas_orfaos': schemas_orfaos,
        'lojas_vazias': lojas_vazias,
        'usuarios_orfaos': usuarios_orfaos,
        'financeiros_orfaos': financeiros_orfaos
    }


if __name__ == '__main__':
    try:
        analisar_orfaos()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
