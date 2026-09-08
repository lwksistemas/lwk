"""Garante coluna is_padrao em locais_atendimento e nomes_agenda (migration 0050).

Uso:
    python manage.py ensure_local_nomeagenda_is_padrao
    python manage.py ensure_local_nomeagenda_is_padrao --slug beta
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION = "0050_local_nomeagenda_is_padrao"
LOCAIS_TABLE = "clinica_beleza_locais_atendimento"
NOMES_TABLE = "clinica_beleza_nomes_agenda"


class Command(BaseCommand):
    help = "Adiciona is_padrao em locais de atendimento e nomes de agenda nos schemas das lojas."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = (
            Loja.objects.filter(is_active=True)
            .exclude(database_name="")
            .exclude(database_name__isnull=True)
        )
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            schema = (loja.database_name or "").replace("-", "_")
            db_name = loja.database_name
            if not schema or not db_name:
                skip += 1
                continue

            # Padrão A: alias próprio da loja (search_path já vem na URL da conexão,
            # autocommit). Sem SET search_path na conexão default compartilhada — mais
            # seguro e pronto para paralelização futura por processo.
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f"  skip {loja.slug}: DB indisponível"))
                continue

            try:
                changed = False
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    for table in (LOCAIS_TABLE, NOMES_TABLE):
                        if not table_exists(cursor, table):
                            continue
                        if column_exists(cursor, table, "is_padrao"):
                            continue
                        cursor.execute(f"""
                            ALTER TABLE {table}
                            ADD COLUMN IF NOT EXISTS is_padrao BOOLEAN NOT NULL DEFAULT FALSE
                        """)
                        self.stdout.write(f"  {loja.slug}: {table}.is_padrao adicionada")
                        changed = True

                    if changed:
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
                else:
                    skip += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  OK {loja.slug} ({loja.nome}) schema={schema}",
                ))
            except Exception as e:
                skip += 1
                self.stdout.write(self.style.ERROR(f"  ERRO {loja.slug}: {e}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s), {skip} ignorada(s)/erro."))
