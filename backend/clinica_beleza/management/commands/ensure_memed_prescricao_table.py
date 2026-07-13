"""Garante a tabela clinica_beleza_prescricoes_memed nos bancos/schemas das lojas.

Cria a tabela (via schema_editor, exatamente como o modelo define) quando ela não
existe e marca a migration 0023_prescricao_memed como aplicada, evitando conflito
quando migrate_all_lojas rodar depois.

Uso:
    python manage.py ensure_memed_prescricao_table
    python manage.py ensure_memed_prescricao_table --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.models import PrescricaoMemed
from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = "0023_prescricao_memed"
TABLE_NAME = "clinica_beleza_prescricoes_memed"




class Command(BaseCommand):
    help = "Cria clinica_beleza_prescricoes_memed nos bancos das lojas (Memed)."

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
                    # A tabela base (clinica_beleza_consultas/patient) precisa existir.
                    if not table_exists(cursor, "clinica_beleza_consultas"):
                        skip += 1
                        continue
                    ja_existia = table_exists(cursor, TABLE_NAME)

                if not ja_existia:
                    with conn.schema_editor() as schema_editor:
                        schema_editor.create_model(PrescricaoMemed)

                with conn.cursor() as cursor:
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
                detalhe = "tabela criada" if not ja_existia else "já existia"
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
