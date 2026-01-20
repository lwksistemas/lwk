#!/usr/bin/env python
"""
Script para criar o banco de dados de suporte no Heroku
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connections

print("=" * 50)
print("Criando banco de dados de suporte...")
print("=" * 50)

# Verificar se o banco existe
try:
    conn = connections['suporte']
    conn.ensure_connection()
    print("✅ Conexão com banco 'suporte' estabelecida")
except Exception as e:
    print(f"⚠️ Erro ao conectar: {e}")
    print("Tentando criar o banco...")

# Executar migrations
try:
    print("\n📦 Aplicando migrations no banco 'suporte'...")
    call_command('migrate', 'suporte', '--database=suporte', verbosity=2)
    print("✅ Migrations aplicadas com sucesso!")
except Exception as e:
    print(f"❌ Erro ao aplicar migrations: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Processo concluído!")
print("=" * 50)
