#!/usr/bin/env python
"""Script para testar clientes no banco"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_local')
django.setup()

from superadmin.models import Loja
from cabeleireiro.models import Cliente
import psycopg2

# Buscar loja
loja = Loja.objects.get(id=90)
print(f"Loja ID: {loja.id}")
print(f"Loja Slug: {loja.slug}")
print(f"Loja database_name: {loja.database_name}")

# Buscar clientes SEM filtro
clientes_all = Cliente.objects.all_without_filter().filter(loja_id=90)
print(f"\nClientes com loja_id=90 (sem filtro): {clientes_all.count()}")
for c in clientes_all:
    print(f"  - ID: {c.id}, Nome: {c.nome}, loja_id: {c.loja_id}")

# Verificar se existem clientes no schema correto
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Verificar schema loja_salao_000172
    cur.execute("SELECT * FROM loja_salao_000172.cabeleireiro_clientes;")
    rows = cur.fetchall()
    print(f"\nClientes no schema loja_salao_000172: {len(rows)}")
    for row in rows:
        print(f"  - {row}")
    
    cur.close()
    conn.close()
