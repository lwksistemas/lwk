#!/usr/bin/env python
"""
Script para corrigir limites de storage para 500 MB
Todas as lojas devem ter limite de 500 MB independente do plano
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, PlanoAssinatura

def main():
    print("=" * 80)
    print("🔧 CORREÇÃO DE LIMITES DE STORAGE PARA 500 MB")
    print("=" * 80)
    print()
    
    # 1. Atualizar todos os planos para 0.5 GB (500 MB)
    print("📋 Atualizando planos...")
    planos = PlanoAssinatura.objects.all()
    
    for plano in planos:
        limite_antigo_gb = plano.espaco_storage_gb
        limite_antigo_mb = limite_antigo_gb * 1024
        
        print(f"\n  Plano: {plano.nome}")
        print(f"    Limite atual: {limite_antigo_gb} GB ({limite_antigo_mb} MB)")
        
        # Atualizar para 500 MB (0.5 GB)
        # Mas como o campo é IntegerField, vamos manter em 1 GB e ajustar as lojas para 500 MB
        if limite_antigo_gb != 1:
            plano.espaco_storage_gb = 1  # 1 GB no plano
            plano.save(update_fields=['espaco_storage_gb'])
            print(f"    ✅ Atualizado para: 1 GB (mas lojas terão 500 MB)")
        else:
            print(f"    ℹ️  Já está em 1 GB")
    
    print()
    print("=" * 80)
    
    # 2. Atualizar todas as lojas para 500 MB
    print("\n🏪 Atualizando lojas...")
    lojas = Loja.objects.all()
    
    total = lojas.count()
    atualizadas = 0
    
    for loja in lojas:
        limite_antigo = loja.storage_limite_mb
        
        if limite_antigo != 500:
            print(f"\n  Loja: {loja.nome} ({loja.slug})")
            print(f"    Plano: {loja.plano.nome if loja.plano else 'Sem plano'}")
            print(f"    Limite atual: {limite_antigo} MB ({limite_antigo / 1024:.2f} GB)")
            print(f"    Uso atual: {loja.storage_usado_mb:.2f} MB")
            
            # Atualizar para 500 MB
            loja.storage_limite_mb = 500
            loja.save(update_fields=['storage_limite_mb'])
            
            print(f"    ✅ Atualizado para: 500 MB")
            atualizadas += 1
        else:
            print(f"  ✓ {loja.nome}: já está em 500 MB")
    
    print()
    print("=" * 80)
    print(f"\n✅ CONCLUÍDO!")
    print(f"   Total de lojas: {total}")
    print(f"   Lojas atualizadas: {atualizadas}")
    print(f"   Lojas já corretas: {total - atualizadas}")
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
