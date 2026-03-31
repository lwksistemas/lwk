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
    'ATOMIC_REQUESTS': False,
    'AUTOCOMMIT': True,
    'CONN_MAX_AGE': 0,
    'CONN_HEALTH_CHECKS': False,
    'TIME_ZONE': None,
}
from django.db import connections
conn = connections[loja.database_name]

with conn.cursor() as c:
    # 1. Colunas da migração 0008 (se não existirem)
    c.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'crm_vendas_oportunidade'
        AND column_name = 'data_fechamento_ganho'
    """)
    if not c.fetchone():
        c.execute("ALTER TABLE crm_vendas_oportunidade ADD COLUMN data_fechamento_ganho DATE NULL")
        c.execute("ALTER TABLE crm_vendas_oportunidade ADD COLUMN data_fechamento_perdido DATE NULL")
        c.execute("ALTER TABLE crm_vendas_oportunidade ADD COLUMN valor_comissao NUMERIC(10,2) NULL")
        c.execute("CREATE INDEX IF NOT EXISTS crm_opor_loja_dtfechganho_idx ON crm_vendas_oportunidade (loja_id, data_fechamento_ganho)")
        c.execute("CREATE INDEX IF NOT EXISTS crm_opor_loja_dtfechperd_idx ON crm_vendas_oportunidade (loja_id, data_fechamento_perdido)")
        print('Colunas 0008 adicionadas')

    # 2. Tabela crm_vendas_config da migração 0009 (se não existir)
    c.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = 'crm_vendas_config'
    """)
    if not c.fetchone():
        c.execute("""
            CREATE TABLE crm_vendas_config (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                origens_leads JSONB NOT NULL DEFAULT '[]',
                etapas_pipeline JSONB NOT NULL DEFAULT '[]',
                colunas_leads JSONB NOT NULL DEFAULT '[]',
                modulos_ativos JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """)
        c.execute("CREATE INDEX crm_config_loja_idx ON crm_vendas_config (loja_id)")
        print('Tabela crm_vendas_config criada')

    # 3. Registrar migrações como aplicadas (evita reexecução)
    for name in ['0007_backfill_vendedor_lead_conta', '0008_add_comissao_data_fechamento_fields', '0009_crmconfig']:
        c.execute("SELECT 1 FROM django_migrations WHERE app = 'crm_vendas' AND name = %s", [name])
        if not c.fetchone():
            c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('crm_vendas', %s, NOW())", [name])
            print(f'Registrada migração {name}')

print('OK')
