#!/usr/bin/env python
"""
Script para limpar usuários órfãos de forma segura
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction

print("=" * 80)
print("🧹 LIMPEZA DE USUÁRIOS ÓRFÃOS")
print("=" * 80)

# IDs dos usuários órfãos identificados
usuarios_orfaos = [156, 167, 168]

print("\n1️⃣ VERIFICANDO USUÁRIOS ÓRFÃOS")
print("-" * 80)

for user_id in usuarios_orfaos:
    try:
        user = User.objects.get(id=user_id)
        print(f"✅ Usuário encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Criado em: {user.date_joined.strftime('%d/%m/%Y %H:%M')}")
        
        # Verificar se tem lojas
        lojas_count = user.lojas_owned.count()
        print(f"   Lojas: {lojas_count}")
        
    except User.DoesNotExist:
        print(f"⚠️  Usuário ID {user_id} não encontrado (já foi excluído)")

print("\n2️⃣ EXCLUINDO USUÁRIOS ÓRFÃOS")
print("-" * 80)

for user_id in usuarios_orfaos:
    try:
        with transaction.atomic():
            user = User.objects.get(id=user_id)
            username = user.username
            
            # Excluir usando SQL direto para evitar problemas com ForeignKeys
            from django.db import connection
            with connection.cursor() as cursor:
                # Excluir sessões do usuário
                cursor.execute("DELETE FROM superadmin_usersession WHERE user_id = %s", [user_id])
                print(f"   ✅ Sessões do usuário {username} excluídas")
                
                # Excluir profissionais vinculados
                cursor.execute("DELETE FROM superadmin_profissionalusuario WHERE user_id = %s", [user_id])
                print(f"   ✅ Vínculos de profissional excluídos")
                
                # Excluir vendedores vinculados
                cursor.execute("DELETE FROM superadmin_vendedorusuario WHERE user_id = %s", [user_id])
                print(f"   ✅ Vínculos de vendedor excluídos")
                
                # Excluir usuário
                cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
                print(f"   ✅ Usuário {username} (ID: {user_id}) excluído")
                
    except User.DoesNotExist:
        print(f"   ⚠️  Usuário ID {user_id} não encontrado")
    except Exception as e:
        print(f"   ❌ Erro ao excluir usuário ID {user_id}: {e}")

print("\n" + "=" * 80)
print("✅ LIMPEZA CONCLUÍDA!")
print("=" * 80)
