#!/usr/bin/env python
"""
Script para verificar se os atalhos foram gerados corretamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja

def verificar_atalhos():
    """Verifica se os atalhos foram gerados corretamente"""
    print("=" * 80)
    print("VERIFICAÇÃO DE ATALHOS - Sistema Híbrido de Acesso às Lojas")
    print("=" * 80)
    print()
    
    # Total de lojas
    total_lojas = Loja.objects.count()
    print(f"📊 Total de lojas: {total_lojas}")
    print()
    
    # Lojas com atalho
    lojas_com_atalho = Loja.objects.exclude(atalho='').count()
    lojas_sem_atalho = Loja.objects.filter(atalho='').count()
    
    print(f"✅ Lojas com atalho: {lojas_com_atalho}")
    print(f"❌ Lojas sem atalho: {lojas_sem_atalho}")
    print()
    
    # Verificar duplicatas
    from django.db.models import Count
    duplicatas = Loja.objects.values('atalho').annotate(
        count=Count('id')
    ).filter(count__gt=1, atalho__isnull=False).exclude(atalho='')
    
    if duplicatas:
        print(f"⚠️  ATENÇÃO: {len(duplicatas)} atalhos duplicados encontrados!")
        for dup in duplicatas:
            print(f"   - '{dup['atalho']}': {dup['count']} lojas")
    else:
        print("✅ Nenhum atalho duplicado encontrado")
    print()
    
    # Listar primeiras 10 lojas
    print("📋 Primeiras 10 lojas:")
    print("-" * 80)
    print(f"{'ID':<5} | {'Nome':<30} | {'Atalho':<20} | {'Slug':<30}")
    print("-" * 80)
    
    for loja in Loja.objects.all()[:10]:
        nome = loja.nome[:30]
        atalho = loja.atalho or '(vazio)'
        slug = loja.slug[:30]
        print(f"{loja.id:<5} | {nome:<30} | {atalho:<20} | {slug:<30}")
    
    print("-" * 80)
    print()
    
    # URLs de exemplo
    if lojas_com_atalho > 0:
        loja_exemplo = Loja.objects.exclude(atalho='').first()
        print("🔗 Exemplo de URLs:")
        print(f"   Atalho simples: https://lwksistemas.com.br/{loja_exemplo.atalho}")
        print(f"   URL completa:   {loja_exemplo.get_url_segura()}")
        print(f"   URL amigável:   {loja_exemplo.get_url_amigavel()}")
    
    print()
    print("=" * 80)
    print("✅ Verificação concluída!")
    print("=" * 80)

if __name__ == '__main__':
    verificar_atalhos()
