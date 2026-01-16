#!/usr/bin/env python
"""Script para criar banco da loja Harmonis"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from django.conf import settings
from django.core.management import call_command
from pathlib import Path
from django.contrib.auth.models import User

# Buscar loja
loja = Loja.objects.get(nome='Harmonis')
print(f"📋 Loja: {loja.nome}")
print(f"📋 Slug: {loja.slug}")
print(f"📋 Database: {loja.database_name}")
print(f"📋 Owner: {loja.owner.username}")
print(f"📋 Email: {loja.owner.email}")
print(f"📋 Senha: {loja.senha_provisoria}")

if loja.database_created:
    print("⚠️  Banco já foi criado!")
    exit(0)

# Configurar banco
db_name = loja.database_name
db_path = settings.BASE_DIR / f'db_{db_name}.sqlite3'

settings.DATABASES[db_name] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': db_path,
    'ATOMIC_REQUESTS': False,
    'AUTOCOMMIT': True,
    'CONN_MAX_AGE': 0,
    'CONN_HEALTH_CHECKS': False,
    'OPTIONS': {},
    'TIME_ZONE': None,
}

print(f"\n🔧 Criando banco: {db_path}")

# Executar migrations
print("📦 Executando migrations...")
call_command('migrate', '--database', db_name, verbosity=1)

# Criar usuário admin da loja
print(f"\n👤 Criando usuário admin...")
try:
    admin_loja = User.objects.db_manager(db_name).create_user(
        username=loja.owner.username,
        email=loja.owner.email,
        password=loja.senha_provisoria,
        is_staff=True
    )
    print(f"✅ Usuário criado: {admin_loja.username}")
except Exception as e:
    print(f"⚠️  Erro ao criar usuário: {e}")

# Marcar como criado
loja.database_created = True
loja.save()

print(f"\n✅ BANCO CRIADO COM SUCESSO!")
print(f"\n🔐 DADOS DE ACESSO:")
print(f"   URL: http://localhost:3000{loja.login_page_url}")
print(f"   Usuário: {loja.owner.username}")
print(f"   Senha: {loja.senha_provisoria}")
print(f"   Email: {loja.owner.email}")
