"""
Garante a tabela clinica_beleza_memed_timbrado nos schemas das lojas.

Uso:
    python manage.py ensure_memed_timbrado_table
    python manage.py ensure_memed_timbrado_table --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = '0025_memed_timbrado'




class Command(BaseCommand):
    help = 'Cria clinica_beleza_memed_timbrado nos bancos das lojas se não existir.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_memed_timbrado'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_memed_timbrado (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                pdf BYTEA NOT NULL,
                                pdf_nome VARCHAR(255) NOT NULL DEFAULT '',
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_memed_timbrado_loja_id_idx ON clinica_beleza_memed_timbrado (loja_id)'
                        )
                    cursor.execute(
                        """
                        INSERT INTO django_migrations (app, name, applied)
                        SELECT 'clinica_beleza', %s, NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM django_migrations
                            WHERE app = 'clinica_beleza' AND name = %s
                        )
                        """,
                        [MIGRATION_NAME, MIGRATION_NAME],
                    )
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'OK loja={loja.id} ({loja.nome})'))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id}: {exc}'))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s), {skip} ignorada(s).'))
