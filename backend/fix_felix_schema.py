#!/usr/bin/env python
"""Script one-off para corrigir schema felix-5889. Executar: heroku run "cd backend && python fix_felix_schema.py" --app lwksistemas"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from superadmin.models import Loja
import dj_database_url

loja = Loja.objects.get(slug__iexact='felix-5889')
schema = loja.database_name.replace('-', '_')
db_url = os.environ.get('DATABASE_URL')
cfg = dj_database_url.config(default=db_url, conn_max_age=0)
settings.DATABASES[loja.database_name] = {
    **cfg,
    'OPTIONS': {'options': f'-c search_path={schema},public'},
    'CONN_MAX_AGE': 0,
}
from django.db import connections
conn = connections[loja.database_name]
with conn.cursor() as c:
    c.execute("DELETE FROM django_migrations WHERE app = %s AND name = %s", ['servicos', '0005_add_loja_isolation'])
    print('Deleted:', c.rowcount)
