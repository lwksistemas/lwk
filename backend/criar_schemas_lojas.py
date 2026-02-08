#!/usr/bin/env python
"""
Script para criar schemas no PostgreSQL para todas as lojas que não têm.

IMPORTANTE: Este script deve ser executado ANTES de criar novas lojas.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def schema_exists(schema_name):
    """Verifica se o schema existe no PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, [schema_name])
        return cursor.fetchone() is not None

def criar_schemas():
    """Cria schemas para todas as lojas que não têm"""
    lojas = Loja.objects.all()
    
    print(f"📋 Total de lojas: {lojas.count()}")
    print("=" * 80)
    
    for loja in lojas:
        schema_name = loja.database_name
        print(f"\n🏪 Loja: {loja.nome}")
        print(f"   Slug: {loja.slug}")
        print(f"   Schema: {schema_name}")
        print(f"   database_created: {loja.database_created}")
        
        # Verificar se schema existe
        if schema_exists(schema_name):
            print(f"   ✅ Schema já existe")
            
            # Marcar como criado se não estiver
            if not loja.database_created:
                loja.database_created = True
                loja.save(update_fields=['database_created'])
                print(f"   ✅ Marcado como database_created=True")
        else:
            print(f"   ⚠️  Schema NÃO existe - criando...")
            
            try:
                with connection.cursor() as cursor:
                    # Criar schema
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                    print(f"   ✅ Schema '{schema_name}' criado")
                    
                    # Marcar como criado
                    loja.database_created = True
                    loja.save(update_fields=['database_created'])
                    print(f"   ✅ Marcado como database_created=True")
                    
            except Exception as e:
                print(f"   ❌ Erro ao criar schema: {e}")
                import traceback
                traceback.print_exc()

def listar_schemas():
    """Lista todos os schemas existentes no PostgreSQL"""
    print("\n" + "=" * 80)
    print("📋 Schemas existentes no PostgreSQL:")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = cursor.fetchall()
        
        for (schema_name,) in schemas:
            print(f"   - {schema_name}")
        
        print(f"\n   Total: {len(schemas)} schemas")

if __name__ == '__main__':
    print("🚀 Iniciando criação de schemas para lojas...")
    print("=" * 80)
    
    criar_schemas()
    listar_schemas()
    
    print("\n" + "=" * 80)
    print("✅ Processo concluído!")
    print("=" * 80)
