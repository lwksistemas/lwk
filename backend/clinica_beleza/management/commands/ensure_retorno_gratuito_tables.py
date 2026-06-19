"""
Garante tabelas/colunas de retorno gratuito (migration 0047) nos schemas das lojas.

Fallback quando migrate_all_lojas não aplica 0047_retorno_gratuito_agenda.
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION = '0047_retorno_gratuito_agenda'


class Command(BaseCommand):
    help = 'Cria config/regras de retorno gratuito e colunas em appointment/consulta (IF NOT EXISTS).'

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

                    changed = False

                    if not table_exists(cursor, 'clinica_beleza_agenda_retorno_config'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_agenda_retorno_config (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                retorno_procedimento_ativo BOOLEAN NOT NULL DEFAULT FALSE,
                                retorno_consulta_ativo BOOLEAN NOT NULL DEFAULT FALSE,
                                dias_retorno_consulta INTEGER NOT NULL DEFAULT 30
                                    CHECK (dias_retorno_consulta >= 0),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_agenda_retorno_config_loja_id_idx '
                            'ON clinica_beleza_agenda_retorno_config (loja_id)'
                        )
                        changed = True

                    if not table_exists(cursor, 'clinica_beleza_retorno_procedimento_regra'):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_retorno_procedimento_regra (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                dias_retorno INTEGER NOT NULL CHECK (dias_retorno >= 1),
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                procedure_id BIGINT NOT NULL
                                    REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
                                CONSTRAINT uniq_retorno_procedimento_loja
                                    UNIQUE (procedure_id, loja_id)
                            )
                        """)
                        cursor.execute(
                            'CREATE INDEX IF NOT EXISTS clinica_beleza_retorno_procedimento_regra_loja_id_idx '
                            'ON clinica_beleza_retorno_procedimento_regra (loja_id)'
                        )
                        changed = True

                    if not column_exists(cursor, 'clinica_beleza_appointment', 'retorno_procedure_id'):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_appointment
                            ADD COLUMN retorno_procedure_id BIGINT NULL
                            REFERENCES clinica_beleza_procedure(id) ON DELETE SET NULL
                        """)
                        changed = True

                    consulta_table = 'clinica_beleza_consultas'
                    if table_exists(cursor, consulta_table):
                        if not column_exists(cursor, consulta_table, 'retorno_gratuito'):
                            cursor.execute("""
                                ALTER TABLE clinica_beleza_consultas
                                ADD COLUMN retorno_gratuito BOOLEAN NOT NULL DEFAULT FALSE
                            """)
                            changed = True
                        if not column_exists(cursor, consulta_table, 'retorno_tipo'):
                            cursor.execute("""
                                ALTER TABLE clinica_beleza_consultas
                                ADD COLUMN retorno_tipo VARCHAR(20) NOT NULL DEFAULT ''
                            """)
                            changed = True

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

                if changed:
                    ok += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'OK loja={loja.id} ({loja.nome}) db={db_name}: retorno gratuito criado/atualizado'
                    ))
                else:
                    skip += 1
                    self.stdout.write(f'OK (já existe) loja={loja.id} ({loja.nome})')
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).'))
