"""
Garante as colunas data_nascimento/sexo em clinica_beleza_professional
(schemas/bancos das lojas), usadas no cadastro do prescritor na Memed.

Adiciona as colunas se não existirem e marca a migration
0024_professional_nascimento_sexo como aplicada, evitando conflito quando
migrate_all_lojas rodar depois.

Uso:
    python manage.py ensure_professional_nascimento_sexo
    python manage.py ensure_professional_nascimento_sexo --slug beleza
"""
from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = '0024_professional_nascimento_sexo'
COLUNAS = (
    ('data_nascimento', 'DATE NULL'),
    ('sexo', 'VARCHAR(1) NULL'),
)


def _table_exists(cursor, table: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = %s LIMIT 1
        """,
        [table],
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s AND column_name = %s LIMIT 1
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


class Command(BaseCommand):
    help = 'Adiciona data_nascimento/sexo em clinica_beleza_professional nos bancos das lojas.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = 0
        skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f'SKIP loja={loja.id}: banco não configurado'))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not _table_exists(cursor, 'clinica_beleza_professional'):
                        skip += 1
                        continue

                    adicionadas = []
                    for coluna, tipo in COLUNAS:
                        if not _column_exists(cursor, 'clinica_beleza_professional', coluna):
                            cursor.execute(
                                f'ALTER TABLE clinica_beleza_professional ADD COLUMN {coluna} {tipo}'
                            )
                            adicionadas.append(coluna)

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
                detalhe = ', '.join(adicionadas) if adicionadas else 'nenhuma nova (já existiam)'
                self.stdout.write(self.style.SUCCESS(
                    f'OK loja={loja.id} ({loja.nome}) db={db_name}: {detalhe}'
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).'))
