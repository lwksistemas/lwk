"""
Garante tabelas de despesas nos schemas das lojas.

Uso:
    python manage.py ensure_despesas_tables
    python manage.py ensure_despesas_tables --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria tabelas de despesas e categorias nos schemas das lojas.'

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
                with connections[db_name].cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_categoriadespesa'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_categoriadespesa (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(100) NOT NULL,
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_categoriadespesa_loja_id_idx '
                            'ON clinica_beleza_categoriadespesa (loja_id)'
                        )

                    if not table_exists(cursor, 'clinica_beleza_despesa'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_despesa (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                descricao VARCHAR(200) NOT NULL,
                                valor NUMERIC(10, 2) NOT NULL,
                                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                                data_vencimento DATE NOT NULL,
                                data_pagamento DATE NULL,
                                forma_pagamento VARCHAR(20) NOT NULL DEFAULT '',
                                observacoes TEXT NOT NULL DEFAULT '',
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                categoria_id BIGINT NULL
                                    REFERENCES clinica_beleza_categoriadespesa(id) ON DELETE SET NULL
                            )
                        """)
                        for idx_sql in (
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_despesa_loja_status_idx '
                            'ON clinica_beleza_despesa (loja_id, status)',
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_despesa_loja_venc_idx '
                            'ON clinica_beleza_despesa (loja_id, data_vencimento)',
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_despesa_loja_pag_idx '
                            'ON clinica_beleza_despesa (loja_id, data_pagamento)',
                        ):
                            cursor.execute(idx_sql)

                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        SELECT 'clinica_beleza', '0035_despesa_categoria', NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM django_migrations
                            WHERE app = 'clinica_beleza' AND name = '0035_despesa_categoria'
                        )
                    """)

                ok += 1
                self.stdout.write(self.style.SUCCESS(f'  OK {loja.slug} ({loja.nome})'))
            except Exception as e:
                skip += 1
                self.stdout.write(self.style.ERROR(f'  ERRO {loja.slug}: {e}'))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s), {skip} ignorada(s)/erro.'))
