#!/usr/bin/env python
"""
Script para limpar lojas órfãs criadas durante testes v1013-v1014.
Lojas: 116-122 (7 lojas)
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def limpar_loja_orfa(loja_id):
    """Remove loja órfã e seu schema"""
    try:
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.database_name.replace('-', '_')
        
        print(f"\n🗑️  Limpando loja {loja_id}: {loja.nome}")
        print(f"   Schema: {schema_name}")
        
        # Excluir schema
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
        print(f"   ✅ Schema excluído")
        
        # Excluir loja
        loja.delete()
        print(f"   ✅ Loja excluída")
        
        return True
    except Loja.DoesNotExist:
        print(f"   ⚠️  Loja {loja_id} não existe")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    """Limpar todas as lojas órfãs"""
    lojas_orfas = [116, 117, 118, 119, 120, 121, 122]
    
    print("=" * 60)
    print("LIMPEZA DE LOJAS ÓRFÃS v1015")
    print("=" * 60)
    print(f"\nLojas a limpar: {lojas_orfas}")
    
    sucesso = 0
    falha = 0
    
    for loja_id in lojas_orfas:
        if limpar_loja_orfa(loja_id):
            sucesso += 1
        else:
            falha += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Sucesso: {sucesso}")
    print(f"❌ Falha: {falha}")
    print("=" * 60)

if __name__ == '__main__':
    main()
