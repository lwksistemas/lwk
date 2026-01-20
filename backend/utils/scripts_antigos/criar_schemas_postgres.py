#!/usr/bin/env python
"""
Script para criar schemas no PostgreSQL e aplicar migrations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from django.db import connection

print("=" * 60)
print("CRIAÇÃO DE SCHEMAS NO POSTGRESQL")
print("=" * 60)

schemas = ['suporte', 'loja_template', 'loja_felix', 'loja_harmonis', 'loja_loja_tech', 'loja_moda_store']

with connection.cursor() as cursor:
    for schema in schemas:
        print(f"\n📁 Criando schema: {schema}")
        try:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            print(f"   ✅ Schema '{schema}' criado/verificado")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")

print("\n" + "=" * 60)
print("✅ SCHEMAS CRIADOS!")
print("=" * 60)
print("\nPróximos passos:")
print("1. Aplicar migrations no schema suporte")
print("2. Aplicar migrations nos schemas das lojas")
print("3. Migrar dados existentes")
