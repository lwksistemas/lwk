"""Garante tabela clinica_beleza_nomes_agenda e coluna nome_agenda_id em appointment.

Necessário quando migrate_all_lojas não aplica 0040_nome_agenda por histórico legado.
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION = "0040_nome_agenda"


class Command(BaseCommand):
    help = "Cria nomes de agenda e FK em appointment (IF NOT EXISTS) nos bancos das lojas."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, "clinica_beleza_appointment"):
                        skip += 1
                        continue

                    changed = False
                    if not table_exists(cursor, "clinica_beleza_nomes_agenda"):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_nomes_agenda (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            "CREATE INDEX IF NOT EXISTS clinica_beleza_nomes_agenda_loja_id_idx "
                            "ON clinica_beleza_nomes_agenda (loja_id)",
                        )
                        changed = True

                    if not column_exists(cursor, "clinica_beleza_appointment", "nome_agenda_id"):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_appointment
                            ADD COLUMN nome_agenda_id BIGINT NULL
                            REFERENCES clinica_beleza_nomes_agenda(id) ON DELETE SET NULL
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
                        f"OK loja={loja.id} ({loja.nome}) db={db_name}: nomes_agenda criado/atualizado",
                    ))
                else:
                    skip += 1
                    self.stdout.write(f"OK (já existe) loja={loja.id} ({loja.nome})")
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"ERRO loja={loja.id} ({loja.nome}): {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s)."))
