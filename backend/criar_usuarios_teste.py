#!/usr/bin/env python
"""
Script para criar usuários de teste no sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

def criar_usuarios_teste():
    print("🚀 Criando usuários de teste...")
    
    # 1. Super Admin
    if not User.objects.filter(username='admin').exists():
        user_admin = User.objects.create_user(
            username='admin',
            email='admin@sistema.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema',
            is_staff=True,
            is_superuser=True
        )
        
        UsuarioSistema.objects.create(
            user=user_admin,
            tipo='superadmin',
            telefone='(11) 99999-0001',
            pode_criar_lojas=True,
            pode_gerenciar_financeiro=True,
            pode_acessar_todas_lojas=True,
            is_active=True
        )
        print("✅ Super Admin criado: admin / admin123")
    else:
        print("⚠️  Super Admin 'admin' já existe")
    
    # 2. Suporte 1
    if not User.objects.filter(username='suporte1').exists():
        user_suporte1 = User.objects.create_user(
            username='suporte1',
            email='suporte1@sistema.com',
            password='suporte123',
            first_name='João',
            last_name='Suporte',
            is_staff=True
        )
        
        UsuarioSistema.objects.create(
            user=user_suporte1,
            tipo='suporte',
            telefone='(11) 99999-0002',
            pode_criar_lojas=False,
            pode_gerenciar_financeiro=False,
            pode_acessar_todas_lojas=True,
            is_active=True
        )
        print("✅ Suporte 1 criado: suporte1 / suporte123")
    else:
        print("⚠️  Usuário 'suporte1' já existe")
    
    # 3. Suporte 2
    if not User.objects.filter(username='suporte2').exists():
        user_suporte2 = User.objects.create_user(
            username='suporte2',
            email='suporte2@sistema.com',
            password='suporte123',
            first_name='Maria',
            last_name='Atendimento',
            is_staff=True
        )
        
        UsuarioSistema.objects.create(
            user=user_suporte2,
            tipo='suporte',
            telefone='(11) 99999-0003',
            pode_criar_lojas=False,
            pode_gerenciar_financeiro=True,
            pode_acessar_todas_lojas=False,
            is_active=True
        )
        print("✅ Suporte 2 criado: suporte2 / suporte123")
    else:
        print("⚠️  Usuário 'suporte2' já existe")
    
    # 4. Super Admin 2
    if not User.objects.filter(username='gerente').exists():
        user_gerente = User.objects.create_user(
            username='gerente',
            email='gerente@sistema.com',
            password='gerente123',
            first_name='Carlos',
            last_name='Gerente',
            is_staff=True,
            is_superuser=True
        )
        
        UsuarioSistema.objects.create(
            user=user_gerente,
            tipo='superadmin',
            telefone='(11) 99999-0004',
            pode_criar_lojas=True,
            pode_gerenciar_financeiro=True,
            pode_acessar_todas_lojas=True,
            is_active=True
        )
        print("✅ Super Admin 2 criado: gerente / gerente123")
    else:
        print("⚠️  Usuário 'gerente' já existe")
    
    # 5. Suporte Inativo
    if not User.objects.filter(username='suporte_inativo').exists():
        user_inativo = User.objects.create_user(
            username='suporte_inativo',
            email='inativo@sistema.com',
            password='inativo123',
            first_name='Pedro',
            last_name='Inativo',
            is_staff=True,
            is_active=False
        )
        
        UsuarioSistema.objects.create(
            user=user_inativo,
            tipo='suporte',
            telefone='(11) 99999-0005',
            pode_criar_lojas=False,
            pode_gerenciar_financeiro=False,
            pode_acessar_todas_lojas=False,
            is_active=False
        )
        print("✅ Suporte Inativo criado: suporte_inativo / inativo123")
    else:
        print("⚠️  Usuário 'suporte_inativo' já existe")
    
    print("\n✅ Processo concluído!")
    print("\n📋 RESUMO DOS USUÁRIOS:")
    print("=" * 60)
    print("Super Admins:")
    print("  - admin / admin123 (Administrador Sistema)")
    print("  - gerente / gerente123 (Carlos Gerente)")
    print("\nSuporte:")
    print("  - suporte1 / suporte123 (João Suporte)")
    print("  - suporte2 / suporte123 (Maria Atendimento)")
    print("  - suporte_inativo / inativo123 (Pedro Inativo - INATIVO)")
    print("=" * 60)

if __name__ == '__main__':
    criar_usuarios_teste()
