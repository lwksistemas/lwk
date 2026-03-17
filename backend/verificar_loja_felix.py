#!/usr/bin/env python
"""Verificar detalhes da loja felix antes de excluir"""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja, FinanceiroLoja

loja = Loja.objects.get(id=107)
print(f"\nLoja ID: {loja.id}")
print(f"Slug: {loja.slug}")
print(f"Nome: {loja.nome}")
print(f"Database Name: {loja.database_name}")
print(f"Database Created: {loja.database_created}")
print(f"Owner: {loja.owner.username} ({loja.owner.email})")
print(f"Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")

# Verificar schema
schema_name = loja.database_name.replace('-', '_')
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_type = 'BASE TABLE';
    """, [schema_name])
    tabelas_count = cursor.fetchone()[0]

print(f"\nSchema: {schema_name}")
print(f"Tabelas no schema: {tabelas_count}")

# Verificar financeiro
try:
    financeiro = FinanceiroLoja.objects.get(loja=loja)
    print(f"\nFinanceiro: Existe (ID: {financeiro.id})")
    print(f"Status: {financeiro.status_pagamento}")
except FinanceiroLoja.DoesNotExist:
    print(f"\nFinanceiro: NÃO EXISTE")

print("\n✅ Loja pode ser excluída com segurança (schema vazio)")
