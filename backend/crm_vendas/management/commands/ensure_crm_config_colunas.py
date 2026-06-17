"""
Garante colunas colunas_contas e colunas_contatos em crm_vendas_config (schemas das lojas).

Uso:
    python manage.py ensure_crm_config_colunas
    python manage.py ensure_crm_config_colunas --slug felix
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

TABLE = 'crm_vendas_config'
COLUMNS = (
    ('colunas_contas', "JSONB NOT NULL DEFAULT '[]'::jsonb"),
    ('colunas_contatos', "JSONB NOT NULL DEFAULT '[]'::jsonb"),
)
MIGRATION = '0062_crmconfig_colunas_contas_contatos'


class Command(BaseCommand):
    help = 'Adiciona colunas_contas/colunas_contatos em crm_vendas_config por loja CRM.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = skip = 0

        for loja in Loja.objects.filter(is_active=True, database_created=True):
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f'Pulando {loja.slug}: DB indisponível'))
                skip += 1
                continue
            try:
                conn = connections[db_name]
                changed = False
                with conn.cursor() as cursor:
                    if not table_exists(cursor, TABLE):
                        self.stdout.write(self.style.WARNING(f'{loja.slug}: tabela {TABLE} ausente'))
                        skip += 1
                        continue
                    for col, ddl in COLUMNS:
                        if not column_exists(cursor, TABLE, col):
                            cursor.execute(f'ALTER TABLE {TABLE} ADD COLUMN {col} {ddl}')
                            self.stdout.write(f'{loja.slug}: coluna {col} adicionada')
                            changed = True
                if changed:
                    try:
                        call_command(
                            'migrate',
                            'crm_vendas',
                            MIGRATION,
                            database=db_name,
                            verbosity=0,
                        )
                    except Exception:
                        pass
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) OK, {skip} pulada(s).'))
