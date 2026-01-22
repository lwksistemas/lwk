#!/usr/bin/env python3
"""
Script para criar a loja felix e associar ao usuário felipe
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
    print("🔍 Criando loja felix para o usuário felipe...")
    
    try:
        # Verificar se o usuário felipe existe
        try:
            usuario_felipe = User.objects.get(username='felipe')
            print(f"✅ Usuário felipe encontrado: {usuario_felipe.username} (ID: {usuario_felipe.id})")
        except User.DoesNotExist:
            print("❌ Usuário felipe não encontrado!")
            return
        
        # Verificar se a loja felix já existe
        try:
            loja_felix = Store.objects.get(slug='felix')
            print(f"⚠️  Loja felix já existe: {loja_felix.name}")
            print(f"   Owner atual: {loja_felix.owner.username if loja_felix.owner else 'Nenhum'}")
            
            # Atualizar o owner se necessário
            if loja_felix.owner != usuario_felipe:
                print("🔧 Atualizando owner da loja felix...")
                loja_felix.owner = usuario_felipe
                loja_felix.save()
                print("✅ Owner atualizado!")
            else:
                print("✅ Felipe já é o owner da loja felix!")
                
        except Store.DoesNotExist:
            print("📝 Criando nova loja felix...")
            
            # Criar a loja felix
            loja_felix = Store.objects.create(
                name='Clínica Felix',
                slug='felix',
                description='Clínica de Estética Felix - Sistema completo de gestão',
                owner=usuario_felipe,
                is_active=True
            )
            print(f"✅ Loja felix criada com sucesso!")
            print(f"   ID: {loja_felix.id}")
            print(f"   Nome: {loja_felix.name}")
            print(f"   Slug: {loja_felix.slug}")
            print(f"   Owner: {loja_felix.owner.username}")
        
        # Verificar o resultado final
        loja_felix.refresh_from_db()
        print(f"\n📊 Status final:")
        print(f"   Loja: {loja_felix.name} (slug: {loja_felix.slug})")
        print(f"   Owner: {loja_felix.owner.username}")
        print(f"   Owner ID: {loja_felix.owner.id}")
        print(f"   Ativa: {loja_felix.is_active}")
        print(f"   Criada em: {loja_felix.created_at}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()