#!/usr/bin/env python
import os, sys, django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

loja = Loja.objects.get(id=90)
print(f'Slug: {loja.slug}')
schema_name = f'loja_{loja.slug.replace("-", "_")}'
print(f'Schema esperado: {schema_name}')

with connection.cursor() as cursor:
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'loja_%'")
    schemas = [row[0] for row in cursor.fetchall()]
    print(f'Schemas existentes: {schemas}')
    
    if schema_name in schemas:
        print(f'\n✅ Schema {schema_name} existe!')
        cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}' AND table_name LIKE 'cabeleireiro_%'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'Tabelas do cabeleireiro: {tables}')
    else:
        print(f'\n❌ Schema {schema_name} NÃO existe!')
