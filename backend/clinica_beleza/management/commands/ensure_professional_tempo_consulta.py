"""Garante coluna tempo_consulta_minutos em clinica_beleza_professional (schemas das lojas).
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION = "0046_professional_tempo_consulta"


class Command(BaseCommand):
    help = "Adiciona tempo_consulta_minutos em clinica_beleza_professional (IF NOT EXISTS)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = 0
        skip = 0

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
                    if not table_exists(cursor, "clinica_beleza_professional"):
                        skip += 1
                        continue

                    if column_exists(cursor, "clinica_beleza_professional", "tempo_consulta_minutos"):
                        skip += 1
                        continue

                    cursor.execute(
                        """
                        ALTER TABLE clinica_beleza_professional
                        ADD COLUMN tempo_consulta_minutos INTEGER NULL
                        """,
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
                        [MIGRATION, MIGRATION],
                    )

                ok += 1
                self.stdout.write(self.style.SUCCESS(
                    f"OK loja={loja.id} ({loja.nome}) db={db_name}: tempo_consulta_minutos adicionada",
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"ERRO loja={loja.id} ({loja.nome}): {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s)."))
