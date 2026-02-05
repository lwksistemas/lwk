#!/usr/bin/env python
"""Script para criar/resetar superadmin"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from superadmin.models import UsuarioSistema
from django.db import transaction

username = 'superadmin'
email = 'superadmin@lwksistemas.com.br'
senha = 'Super@2026'
nome = 'Super'
sobrenome = 'Admin'

print('=' * 60)
print('🔧 CRIANDO/RESETANDO SUPERADMIN')
print('=' * 60)

# Verificar se já existe
user = User.objects.filter(username=username).first()

if user:
    print(f'\n✅ User "{username}" encontrado')
    print(f'   - ID: {user.id}')
    print(f'   - Email: {user.email}')
    print(f'   - is_active: {user.is_active}')
    
    # Resetar senha
    user.set_password(senha)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.email = email
    user.first_name = nome
    user.last_name = sobrenome
    user.save()
    print(f'\n✅ Senha e permissões atualizadas')
    
    # Verificar/criar perfil
    perfil = UsuarioSistema.objects.filter(user=user).first()
    if not perfil:
        perfil = UsuarioSistema.objects.create(
            user=user,
            tipo='superadmin',
            senha_provisoria=senha,
            senha_foi_alterada=False,
            pode_criar_lojas=True,
            pode_gerenciar_financeiro=True,
            pode_acessar_todas_lojas=True,
            is_active=True
        )
        print(f'✅ Perfil UsuarioSistema criado')
    else:
        perfil.tipo = 'superadmin'
        perfil.senha_provisoria = senha
        perfil.senha_foi_alterada = False
        perfil.pode_criar_lojas = True
        perfil.pode_gerenciar_financeiro = True
        perfil.pode_acessar_todas_lojas = True
        perfil.is_active = True
        perfil.save()
        print(f'✅ Perfil UsuarioSistema atualizado')
else:
    print(f'\n📝 Criando novo user "{username}"...')
    with transaction.atomic():
        # Criar User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f'✅ User criado')
        
        # Criar UsuarioSistema
        perfil = UsuarioSistema.objects.create(
            user=user,
            tipo='superadmin',
            senha_provisoria=senha,
            senha_foi_alterada=False,
            pode_criar_lojas=True,
            pode_gerenciar_financeiro=True,
            pode_acessar_todas_lojas=True,
            is_active=True
        )
        print(f'✅ Perfil criado')

# Testar autenticação
print(f'\n🔐 Testando autenticação...')
auth_user = authenticate(username=username, password=senha)

if auth_user:
    print(f'✅ AUTENTICAÇÃO FUNCIONANDO!')
else:
    print(f'❌ ERRO NA AUTENTICAÇÃO')
    sys.exit(1)

print('\n' + '=' * 60)
print('🎉 SUPERADMIN PRONTO!')
print('=' * 60)
print(f'URL: https://lwksistemas.com.br/superadmin/login')
print(f'Usuário: {username}')
print(f'Senha: {senha}')
print('=' * 60)
print('\n⚠️  IMPORTANTE: Troque a senha após o primeiro acesso!')
print('=' * 60)
