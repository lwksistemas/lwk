"""
Garante coluna config_acesso em crm_vendas_vendedor (schemas das lojas CRM).

Remove registros órfãos de clinica_beleza em django_migrations quando o schema
não tem tabelas de clínica — evita bloquear migrate em lojas CRM (ex.: Felix).

Uso:
    python manage.py ensure_vendedor_config_acesso
    python manage.py ensure_vendedor_config_acesso --slug felix
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

TABLE = 'crm_vendas_vendedor'
COLUMN = 'config_acesso'
DDL = "JSONB NOT NULL DEFAULT '{}'::jsonb"
MIGRATION = '0066_vendedor_config_acesso'


def _limpar_migrations_clinica_orfas(cursor) -> int:
    """Remove clinica_beleza de django_migrations se não houver tabelas de clínica."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name LIKE 'clinica_beleza_%'
        """
    )
    if (cursor.fetchone() or [0])[0] > 0:
        return 0
    cursor.execute("DELETE FROM django_migrations WHERE app = %s", ['clinica_beleza'])
    return cursor.rowcount


class Command(BaseCommand):
    help = 'Adiciona config_acesso em crm_vendas_vendedor e limpa migrations clinica órfãs.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = skip = 0

        qs = Loja.objects.filter(is_active=True, database_created=True).select_related('tipo_loja')
        for loja in qs:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            tipo = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
            if tipo != 'crm-vendas':
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
                    removed = _limpar_migrations_clinica_orfas(cursor)
                    if removed:
                        self.stdout.write(
                            f'{loja.slug}: removidos {removed} registro(s) clinica_beleza órfão(s)'
                        )
                        changed = True

                    if not table_exists(cursor, TABLE):
                        self.stdout.write(self.style.WARNING(f'{loja.slug}: tabela {TABLE} ausente'))
                        skip += 1
                        continue

                    if not column_exists(cursor, TABLE, COLUMN):
                        cursor.execute(f'ALTER TABLE {TABLE} ADD COLUMN {COLUMN} {DDL}')
                        self.stdout.write(f'{loja.slug}: coluna {COLUMN} adicionada')
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
            finally:
                if db_name in connections:
                    try:
                        connections[db_name].close()
                    except Exception:
                        pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) OK, {skip} pulada(s).'))
