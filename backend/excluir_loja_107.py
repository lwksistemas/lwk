#!/usr/bin/env python
"""Excluir loja órfã ID 107"""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from superadmin.models import Loja

print("\n" + "="*80)
print("EXCLUSÃO DE LOJA ÓRFÃ")
print("="*80 + "\n")

try:
    loja = Loja.objects.get(id=107)
    
    print(f"Loja encontrada:")
    print(f"  ID: {loja.id}")
    print(f"  Slug: {loja.slug}")
    print(f"  Nome: {loja.nome}")
    print(f"  Owner: {loja.owner.username} ({loja.owner.email})")
    print()
    
    # Excluir loja (signals fazem a limpeza)
    loja.delete()
    
    print("✅ Loja excluída com sucesso!")
    print("   - Schema PostgreSQL removido")
    print("   - Owner removido (se órfão)")
    print("   - Dados relacionados removidos")
    print()
    
except Loja.DoesNotExist:
    print("❌ Loja ID 107 não encontrada (já foi excluída)")
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
