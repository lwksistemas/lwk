#!/usr/bin/env python
"""
Script para excluir a loja órfã ID 109 (FELIX REPRESENTACOES E COMERCIO LTDA).
Criada durante teste de criação de loja com backend corrompido.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def excluir_loja_109():
    """Exclui a loja órfã ID 109."""
    try:
        loja = Loja.objects.get(id=109)
        print(f"\n🔍 Loja encontrada:")
        print(f"   - ID: {loja.id}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Nome: {loja.nome}")
        print(f"   - Schema: loja_{loja.slug}")
        
        schema_name = f"loja_{loja.slug}"
        
        # Verificar se schema existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            schema_exists = cursor.fetchone()
        
        if schema_exists:
            print(f"\n⚠️  Schema '{schema_name}' existe no PostgreSQL")
            
            # Verificar se tem tabelas
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, [schema_name])
                num_tables = cursor.fetchone()[0]
            
            print(f"   - Tabelas no schema: {num_tables}")
            
            if num_tables == 0:
                print(f"\n🗑️  Excluindo schema vazio '{schema_name}'...")
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                print(f"✅ Schema '{schema_name}' excluído")
            else:
                print(f"\n⚠️  Schema tem {num_tables} tabelas, será excluído com CASCADE")
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                print(f"✅ Schema '{schema_name}' e suas tabelas excluídos")
        else:
            print(f"\n✅ Schema '{schema_name}' não existe no PostgreSQL")
        
        # Excluir loja (CASCADE vai excluir usuários e financeiro)
        print(f"\n🗑️  Excluindo loja ID {loja.id}...")
        loja.delete()
        print(f"✅ Loja ID {loja.id} excluída com sucesso")
        
        print("\n" + "="*80)
        print("✅ LOJA ÓRFÃ 109 EXCLUÍDA COM SUCESSO")
        print("="*80)
        
    except Loja.DoesNotExist:
        print("\n❌ Loja ID 109 não encontrada")
    except Exception as e:
        print(f"\n❌ Erro ao excluir loja: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    excluir_loja_109()
