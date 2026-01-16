#!/usr/bin/env python
"""
Script para configurar os 3 bancos de dados isolados
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User, Group
from stores.models import Store
from products.models import Product

def setup_databases():
    print("=" * 60)
    print("CONFIGURANDO SISTEMA MULTI-DATABASE")
    print("=" * 60)
    
    # ========================================
    # BANCO 1: Super Admin (default)
    # ========================================
    print("\n📊 BANCO 1: Super Admin (default)")
    print("-" * 60)
    
    print("Executando migrations no banco 'default'...")
    call_command('migrate', '--database', 'default', verbosity=0)
    
    # Criar super admin
    if not User.objects.db_manager('default').filter(username='superadmin').exists():
        superadmin = User.objects.db_manager('default').create_superuser(
            username='superadmin',
            email='superadmin@system.com',
            password='super123'
        )
        print(f"✅ Super Admin criado: superadmin / super123")
    else:
        print("ℹ️  Super Admin já existe")
    
    # ========================================
    # BANCO 2: Suporte
    # ========================================
    print("\n📊 BANCO 2: Suporte")
    print("-" * 60)
    
    print("Executando migrations no banco 'suporte'...")
    call_command('migrate', '--database', 'suporte', verbosity=0)
    
    # Criar usuário de suporte
    if not User.objects.db_manager('suporte').filter(username='suporte').exists():
        suporte_user = User.objects.db_manager('suporte').create_user(
            username='suporte',
            email='suporte@system.com',
            password='suporte123',
            is_staff=True
        )
        print(f"✅ Usuário de Suporte criado: suporte / suporte123")
        
        # Criar grupo de suporte (sem adicionar ao usuário por causa de FK)
        Group.objects.using('suporte').get_or_create(name='suporte')
        print(f"✅ Grupo 'suporte' criado")
    else:
        print("ℹ️  Usuário de Suporte já existe")
    
    # ========================================
    # BANCO 3: Template de Loja
    # ========================================
    print("\n📊 BANCO 3: Template de Loja")
    print("-" * 60)
    
    print("Executando migrations no banco 'loja_template'...")
    call_command('migrate', '--database', 'loja_template', verbosity=0)
    print("✅ Template de loja configurado")
    
    # ========================================
    # CRIAR LOJAS COM BANCOS ISOLADOS
    # ========================================
    print("\n📊 CRIANDO LOJAS COM BANCOS ISOLADOS")
    print("-" * 60)
    
    lojas_config = [
        {
            'slug': 'loja-tech',
            'nome': 'Loja Tech',
            'descricao': 'Produtos de tecnologia',
            'username': 'admin_tech',
            'password': 'tech123',
            'produtos': [
                {'nome': 'Notebook Dell', 'preco': 3499.90, 'estoque': 10},
                {'nome': 'Mouse Logitech', 'preco': 89.90, 'estoque': 50},
                {'nome': 'Teclado Mecânico', 'preco': 299.90, 'estoque': 25},
            ]
        },
        {
            'slug': 'moda-store',
            'nome': 'Moda Store',
            'descricao': 'Roupas e acessórios',
            'username': 'admin_moda',
            'password': 'moda123',
            'produtos': [
                {'nome': 'Camiseta Básica', 'preco': 49.90, 'estoque': 100},
                {'nome': 'Calça Jeans', 'preco': 149.90, 'estoque': 40},
                {'nome': 'Tênis Esportivo', 'preco': 249.90, 'estoque': 30},
            ]
        },
    ]
    
    for loja_config in lojas_config:
        criar_loja_isolada(loja_config)
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print_credenciais()


def get_database_config(db_path):
    """Retorna configuração completa de banco de dados"""
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'OPTIONS': {},
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }


def criar_loja_isolada(config):
    """Cria uma loja com banco de dados isolado"""
    slug = config['slug']
    db_name = f'loja_{slug}'
    
    print(f"\n🏪 Criando loja: {config['nome']} ({slug})")
    
    # Adicionar banco às configurações
    from django.conf import settings
    from pathlib import Path
    
    db_path = settings.BASE_DIR / f'db_{db_name}.sqlite3'
    
    if db_name not in settings.DATABASES:
        settings.DATABASES[db_name] = get_database_config(db_path)
    
    # Executar migrations no banco da loja
    print(f"  Executando migrations em '{db_name}'...")
    call_command('migrate', '--database', db_name, verbosity=0)
    
    # Criar usuário admin da loja
    if not User.objects.db_manager(db_name).filter(username=config['username']).exists():
        user = User.objects.db_manager(db_name).create_user(
            username=config['username'],
            email=f"{config['username']}@{slug}.com",
            password=config['password'],
            is_staff=True
        )
        print(f"  ✅ Usuário criado: {config['username']} / {config['password']}")
    else:
        user = User.objects.using(db_name).get(username=config['username'])
        print(f"  ℹ️  Usuário já existe: {config['username']}")
    
    # Criar loja
    if not Store.objects.using(db_name).filter(slug=slug).exists():
        store = Store.objects.using(db_name).create(
            name=config['nome'],
            slug=slug,
            description=config['descricao'],
            owner=user
        )
        print(f"  ✅ Loja criada: {config['nome']}")
        
        # Criar produtos
        for prod_config in config['produtos']:
            Product.objects.using(db_name).create(
                store=store,
                name=prod_config['nome'],
                slug=prod_config['nome'].lower().replace(' ', '-'),
                price=prod_config['preco'],
                stock=prod_config['estoque'],
                description=f"Descrição do produto {prod_config['nome']}"
            )
        print(f"  ✅ {len(config['produtos'])} produtos criados")
    else:
        print(f"  ℹ️  Loja já existe: {config['nome']}")
    
    print(f"  📁 Banco: {db_path}")


def print_credenciais():
    """Imprime as credenciais de acesso"""
    print("\n📝 CREDENCIAIS DE ACESSO:")
    print("-" * 60)
    
    print("\n1️⃣  SUPER ADMIN (Banco: default)")
    print("   URL: http://localhost:3000/superadmin/login")
    print("   Usuário: superadmin")
    print("   Senha: super123")
    
    print("\n2️⃣  SUPORTE (Banco: suporte)")
    print("   URL: http://localhost:3000/suporte/login")
    print("   Usuário: suporte")
    print("   Senha: suporte123")
    
    print("\n3️⃣  LOJA TECH (Banco: loja_loja-tech)")
    print("   URL: http://localhost:3000/loja/login?slug=loja-tech")
    print("   Usuário: admin_tech")
    print("   Senha: tech123")
    
    print("\n4️⃣  MODA STORE (Banco: loja_moda-store)")
    print("   URL: http://localhost:3000/loja/login?slug=moda-store")
    print("   Usuário: admin_moda")
    print("   Senha: moda123")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        setup_databases()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
