"""
Garante coluna numero_nota, dias_alerta_validade e tabela consulta_produto nos schemas das lojas.

Uso:
    python manage.py ensure_estoque_produto_fields
    python manage.py ensure_estoque_produto_fields --slug clinicaharmonis
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connection

from clinica_beleza.schema_ensure import (
    CONSULTA_TABLE,
    PRODUTO_ESTOQUE_TABLE,
    column_exists,
    ensure_consulta_produto_utilizado_table,
    table_exists,
)
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona colunas em produtoestoque e tabela consulta_produto nos schemas das lojas.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = (
            Loja.objects.filter(is_active=True)
            .exclude(database_name='')
            .exclude(database_name__isnull=True)
        )
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            schema = (loja.database_name or '').replace('-', '_')
            if not schema:
                skip += 1
                continue
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema}", public')

                    if not table_exists(cursor, PRODUTO_ESTOQUE_TABLE):
                        self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: sem tabela estoque'))
                        skip += 1
                        continue

                    if not column_exists(cursor, PRODUTO_ESTOQUE_TABLE, 'numero_nota'):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_produtoestoque
                            ADD COLUMN IF NOT EXISTS numero_nota VARCHAR(50) NOT NULL DEFAULT ''
                        """)
                        self.stdout.write(f'  {loja.slug}: coluna numero_nota adicionada')
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT 'clinica_beleza', '0034_consulta_produto_numero_nota', NOW()
                            WHERE NOT EXISTS (
                                SELECT 1 FROM django_migrations
                                WHERE app = 'clinica_beleza'
                                  AND name = '0034_consulta_produto_numero_nota'
                            )
                        """)

                    if not column_exists(cursor, PRODUTO_ESTOQUE_TABLE, 'dias_alerta_validade'):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_produtoestoque
                            ADD COLUMN IF NOT EXISTS dias_alerta_validade INTEGER NOT NULL DEFAULT 90
                        """)
                        self.stdout.write(f'  {loja.slug}: coluna dias_alerta_validade adicionada')
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT 'clinica_beleza', '0051_produto_dias_alerta_validade', NOW()
                            WHERE NOT EXISTS (
                                SELECT 1 FROM django_migrations
                                WHERE app = 'clinica_beleza'
                                  AND name = '0051_produto_dias_alerta_validade'
                            )
                        """)

                    if (
                        table_exists(cursor, CONSULTA_TABLE)
                        and ensure_consulta_produto_utilizado_table(cursor)
                        and table_exists(cursor, 'clinica_beleza_consultaprodutoutilizado')
                    ):
                        self.stdout.write(f'  {loja.slug}: tabela consulta_produto OK')
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'  skip {loja.slug}: sem tabela {CONSULTA_TABLE}'
                        ))

                connection.commit()
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'  OK {loja.slug} ({loja.nome}) schema={schema}'))
            except Exception as e:
                skip += 1
                with suppress(Exception):
                    connection.rollback()
                self.stdout.write(self.style.ERROR(f'  ERRO {loja.slug}: {e}'))

        with suppress(Exception):
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s), {skip} ignorada(s)/erro.'))
