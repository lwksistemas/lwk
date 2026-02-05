#!/bin/bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings_local python manage.py shell << 'EOF'
from superadmin.models import Loja
from cabeleireiro.models import Cliente

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
EOF
