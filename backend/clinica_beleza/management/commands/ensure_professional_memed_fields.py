"""Garante as colunas de prescritor Memed em clinica_beleza_professional
(schemas/bancos das lojas): conselho, conselho_uf, cpf.

Adiciona as colunas se não existirem e marca a migration
0022_professional_conselho_cpf como aplicada, evitando conflito quando
migrate_all_lojas rodar depois.

Uso:
    python manage.py ensure_professional_memed_fields
    python manage.py ensure_professional_memed_fields --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = "0022_professional_conselho_cpf"
COLUNAS = (
    ("conselho", "VARCHAR(10) NULL"),
    ("conselho_uf", "VARCHAR(2) NULL"),
    ("cpf", "VARCHAR(14) NULL"),
)




class Command(BaseCommand):
    help = "Adiciona conselho/conselho_uf/cpf em clinica_beleza_professional nos bancos das lojas."

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
                self.stdout.write(self.style.WARNING(f"SKIP loja={loja.id}: banco não configurado"))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, "clinica_beleza_professional"):
                        skip += 1
                        continue

                    adicionadas = []
                    for coluna, tipo in COLUNAS:
                        if not column_exists(cursor, "clinica_beleza_professional", coluna):
                            cursor.execute(
                                f"ALTER TABLE clinica_beleza_professional ADD COLUMN {coluna} {tipo}",
                            )
                            adicionadas.append(coluna)

                    # Marca a migration como aplicada para não conflitar com migrate_all_lojas.
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
                detalhe = ", ".join(adicionadas) if adicionadas else "nenhuma nova (já existiam)"
                self.stdout.write(self.style.SUCCESS(
                    f"OK loja={loja.id} ({loja.nome}) db={db_name}: {detalhe}",
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"ERRO loja={loja.id} ({loja.nome}): {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s)."))
