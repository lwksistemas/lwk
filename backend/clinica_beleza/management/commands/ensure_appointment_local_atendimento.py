"""
Garante coluna local_atendimento_id em clinica_beleza_appointment (schemas das lojas).

Necessário quando migrate_all_lojas não aplica 0041 por histórico legado.
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION = '0041_appointment_local_atendimento'


class Command(BaseCommand):
    help = 'Adiciona local_atendimento_id em clinica_beleza_appointment (IF NOT EXISTS).'

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
                    if not table_exists(cursor, 'clinica_beleza_appointment'):
                        skip += 1
                        continue
                    if not table_exists(cursor, 'clinica_beleza_locais_atendimento'):
                        skip += 1
                        continue

                    if column_exists(cursor, 'clinica_beleza_appointment', 'local_atendimento_id'):
                        skip += 1
                        self.stdout.write(f'OK (já existe) loja={loja.id} ({loja.nome})')
                        continue

                    cursor.execute("""
                        ALTER TABLE clinica_beleza_appointment
                        ADD COLUMN local_atendimento_id BIGINT NULL
                        REFERENCES clinica_beleza_locais_atendimento(id) ON DELETE SET NULL
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
                        [MIGRATION, MIGRATION],
                    )

                ok += 1
                self.stdout.write(self.style.SUCCESS(
                    f'OK loja={loja.id} ({loja.nome}) db={db_name}: local_atendimento_id adicionada'
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).'))
