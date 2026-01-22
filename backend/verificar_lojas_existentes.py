#!/usr/bin/env python3
"""
Script para verificar quais lojas existem no banco de dados
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
    print("🔍 Verificando lojas existentes...")
    
    try:
        # Listar todas as lojas
        lojas = Store.objects.all()
        print(f"📊 Total de lojas encontradas: {lojas.count()}")
        
        for loja in lojas:
            print(f"   - ID: {loja.id} | Slug: '{loja.slug}' | Nome: '{loja.name}' | Owner: {loja.owner.username if loja.owner else 'Nenhum'}")
        
        print("\n🔍 Verificando usuários existentes...")
        usuarios = User.objects.all()
        print(f"📊 Total de usuários encontrados: {usuarios.count()}")
        
        for usuario in usuarios:
            print(f"   - ID: {usuario.id} | Username: '{usuario.username}' | Email: '{usuario.email}' | Superuser: {usuario.is_superuser}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()