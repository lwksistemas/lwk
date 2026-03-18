#!/usr/bin/env python
"""Script para excluir loja órfã ID 113."""
import os, sys, django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

loja = Loja.objects.get(id=113)
schema_name = f"loja_{loja.slug}"
print(f"Excluindo loja {loja.id} ({loja.nome}) - Schema: {schema_name}")

with connection.cursor() as cursor:
    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
print(f"✅ Schema excluído")

loja.delete()
print(f"✅ Loja excluída")
