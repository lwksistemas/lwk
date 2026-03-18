#!/usr/bin/env python
"""
Script para excluir loja órfã ID 112 (schema vazio).
"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def excluir_loja_112():
    """Exclui loja 112 e seu schema."""
    try:
        loja = Loja.objects.get(id=112)
        schema_name = f"loja_{loja.slug}"
        
        print(f"\n🗑️  Excluindo loja órfã:")
        print(f"   - ID: {loja.id}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Nome: {loja.nome}")
        print(f"   - Schema: {schema_name}")
        
        # Excluir schema
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
        print(f"✅ Schema '{schema_name}' excluído")
        
        # Excluir loja
        loja.delete()
        print(f"✅ Loja {loja.id} excluída do banco")
        
        print(f"\n✅ Loja órfã 112 excluída com sucesso!")
        return True
        
    except Loja.DoesNotExist:
        print("❌ Loja 112 não encontrada")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    excluir_loja_112()
