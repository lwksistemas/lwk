#!/usr/bin/env python3
"""
Script para verificar e corrigir o owner da loja felix
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.contrib.auth.models import User
from stores.models import Store

def main():
    print("🔍 Verificando loja felix e usuário felipe...")
    
    try:
        # Verificar se a loja felix existe
        try:
            loja_felix = Store.objects.get(slug='felix')
            print(f"✅ Loja felix encontrada: {loja_felix.name}")
            print(f"   Owner atual: {loja_felix.owner.username if loja_felix.owner else 'Nenhum'}")
            print(f"   ID da loja: {loja_felix.id}")
        except Store.DoesNotExist:
            print("❌ Loja felix não encontrada!")
            return
        
        # Verificar se o usuário felipe existe
        try:
            usuario_felipe = User.objects.get(username='felipe')
            print(f"✅ Usuário felipe encontrado: {usuario_felipe.username}")
            print(f"   ID do usuário: {usuario_felipe.id}")
            print(f"   Email: {usuario_felipe.email}")
        except User.DoesNotExist:
            print("❌ Usuário felipe não encontrado!")
            return
        
        # Verificar se felipe é o owner da loja felix
        if loja_felix.owner == usuario_felipe:
            print("✅ Felipe já é o owner da loja felix!")
        else:
            print(f"⚠️  Felipe NÃO é o owner da loja felix")
            print(f"   Owner atual: {loja_felix.owner.username if loja_felix.owner else 'Nenhum'}")
            
            # Corrigir o owner
            print("🔧 Corrigindo owner da loja felix...")
            loja_felix.owner = usuario_felipe
            loja_felix.save()
            print("✅ Owner corrigido! Felipe agora é o owner da loja felix")
        
        # Verificar novamente
        loja_felix.refresh_from_db()
        print(f"\n📊 Status final:")
        print(f"   Loja: {loja_felix.name} (slug: {loja_felix.slug})")
        print(f"   Owner: {loja_felix.owner.username}")
        print(f"   Owner ID: {loja_felix.owner.id}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()