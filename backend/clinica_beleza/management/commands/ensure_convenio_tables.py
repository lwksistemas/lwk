"""
Garante tabelas de convênio e coluna modo nos schemas das lojas.

Uso:
    python manage.py ensure_convenio_tables
    python manage.py ensure_convenio_tables --slug beleza
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATIONS = ('0032_convenio', '0033_convenioprocedimentopreco_modo')


class Command(BaseCommand):
    help = 'Cria tabelas de convênio e coluna modo nos schemas das lojas.'

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
                    if not table_exists(cursor, 'clinica_beleza_convenios'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_convenios (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                codigo VARCHAR(50) NOT NULL DEFAULT '',
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_convenios_loja_id_idx '
                            'ON clinica_beleza_convenios (loja_id)'
                        )

                    if not table_exists(cursor, 'clinica_beleza_convenio_procedimento_precos'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_convenio_procedimento_precos (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                convenio_id BIGINT NOT NULL REFERENCES clinica_beleza_convenios(id) ON DELETE CASCADE,
                                procedure_id BIGINT NOT NULL REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
                                modo VARCHAR(15) NOT NULL DEFAULT 'fixo',
                                preco NUMERIC(10, 2) NOT NULL,
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                CONSTRAINT uniq_convenio_procedure_loja UNIQUE (convenio_id, procedure_id, loja_id)
                            )
                        """)
                    elif not column_exists(cursor, 'clinica_beleza_convenio_procedimento_precos', 'modo'):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_convenio_procedimento_precos
                            ADD COLUMN modo VARCHAR(15) NOT NULL DEFAULT 'fixo'
                        """)

                    for table in (
                        'clinica_beleza_patient',
                        'clinica_beleza_appointment',
                        'clinica_beleza_consultas',
                    ):
                        if table_exists(cursor, table) and not column_exists(cursor, table, 'convenio_id'):
                            cursor.execute(f"""
                                ALTER TABLE {table}
                                ADD COLUMN convenio_id BIGINT NULL
                                REFERENCES clinica_beleza_convenios(id) ON DELETE SET NULL
                            """)

                    for mig in MIGRATIONS:
                        cursor.execute(
                            """
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT 'clinica_beleza', %s, NOW()
                            WHERE NOT EXISTS (
                                SELECT 1 FROM django_migrations
                                WHERE app = 'clinica_beleza' AND name = %s
                            )
                            """,
                            [mig, mig],
                        )

                ok += 1
                self.stdout.write(self.style.SUCCESS(f'   ✓ {loja.slug} ({db_name})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ {loja.slug}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nConcluído: {ok} loja(s), {skip} ignorada(s).'))
