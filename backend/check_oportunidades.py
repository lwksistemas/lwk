#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crm_vendas.models import Oportunidade
from stores.models import Loja
from django.db import connection

# Buscar loja
loja = Loja.objects.get(cnpj='41449198000172')
print(f"Loja: {loja.nome} (Schema: {loja.database_name})")

# Conectar ao schema da loja
connection.set_tenant(loja)

# Contar oportunidades
total = Oportunidade.objects.count()
print(f"\nTotal de oportunidades: {total}")

if total > 0:
    print("\nÚltimas 10 oportunidades:")
    for o in Oportunidade.objects.order_by('-created_at')[:10]:
        print(f"  ID: {o.id} | Título: {o.titulo} | Etapa: {o.etapa} | Criado: {o.created_at}")
else:
    print("\nNenhuma oportunidade encontrada!")
