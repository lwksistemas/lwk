#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context
from crm_vendas.models import Lead

# Ver qual schema está ativo
print(f"Schema atual: {connection.schema_name}")

# Listar todos os schemas
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
    """)
    schemas = [row[0] for row in cursor.fetchall()]
    print(f"\nSchemas disponíveis ({len(schemas)}): {schemas[:10]}")

# Verificar dados em cada schema
print("\n=== PROCURANDO LEADS ===")
for schema in schemas[:20]:
    try:
        with schema_context(schema):
            count = Lead.objects.count()
            if count > 0:
                print(f"✅ Schema '{schema}': {count} leads")
    except Exception as e:
        pass

print("\nBusca concluída!")
