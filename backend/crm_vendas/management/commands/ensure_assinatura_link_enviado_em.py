"""Garante coluna link_enviado_em em crm_vendas_assinatura_digital nos schemas das lojas.

Uso:
    python manage.py ensure_assinatura_link_enviado_em
    python manage.py ensure_assinatura_link_enviado_em --slug felix
"""
import contextlib

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

TABLE = "crm_vendas_assinatura_digital"
COLUMN = "link_enviado_em"
DDL = "TIMESTAMPTZ NULL"
MIGRATION = "0063_assinatura_digital_link_enviado_em"


class Command(BaseCommand):
    help = "Adiciona link_enviado_em em crm_vendas_assinatura_digital por loja CRM."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        ok = skip = changed = 0

        for loja in Loja.objects.filter(is_active=True, database_created=True):
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f"Pulando {loja.slug}: DB indisponível"))
                skip += 1
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, TABLE):
                        self.stdout.write(self.style.WARNING(f"{loja.slug}: tabela {TABLE} ausente"))
                        skip += 1
                        continue
                    if not column_exists(cursor, TABLE, COLUMN):
                        cursor.execute(f"ALTER TABLE {TABLE} ADD COLUMN {COLUMN} {DDL}")
                        conn.commit()
                        self.stdout.write(
                            self.style.SUCCESS(f"{loja.slug}: coluna {COLUMN} adicionada em {TABLE}"),
                        )
                        changed += 1
                        with contextlib.suppress(Exception):
                            call_command(
                                "migrate",
                                "crm_vendas",
                                MIGRATION,
                                database=db_name,
                                verbosity=0,
                            )
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{loja.slug}: {exc}"))
                skip += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído: {ok} loja(s) OK, {changed} alterada(s), {skip} pulada(s).",
            ),
        )
