"""
Garante coluna local_atendimento_id em clinica_beleza_professional_commissions (comissão por local).

Uso:
    python manage.py ensure_professional_commission_local
    python manage.py ensure_professional_commission_local --slug beleza
"""
from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = '0031_professional_commission_local'


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


class Command(BaseCommand):
    help = 'Adiciona local_atendimento_id em comissões dos profissionais nos schemas das lojas.'

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
                    if not _column_exists(
                        cursor, 'clinica_beleza_professional_commissions', 'local_atendimento_id',
                    ):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_professional_commissions
                            ADD COLUMN local_atendimento_id BIGINT NULL
                            REFERENCES clinica_beleza_locais_atendimento(id) ON DELETE CASCADE
                        """)
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS
                            clinica_beleza_prof_comm_local_id_idx
                            ON clinica_beleza_professional_commissions (local_atendimento_id)
                        """)
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
                self.stdout.write(self.style.SUCCESS(f'   ✓ {loja.slug} ({db_name})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ {loja.slug}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nConcluído: {ok} loja(s), {skip} ignorada(s).'))
