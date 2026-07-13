"""Garante coluna canal_assinatura_vendedor em proposta/contrato nos schemas das lojas.

Uso:
    python manage.py ensure_canal_assinatura_vendedor
    python manage.py ensure_canal_assinatura_vendedor --slug felix
"""
import contextlib

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

TABLES = ("crm_vendas_proposta", "crm_vendas_contrato")
COLUMN = "canal_assinatura_vendedor"
DDL = "VARCHAR(20) NOT NULL DEFAULT 'email'"


class Command(BaseCommand):
    help = "Adiciona canal_assinatura_vendedor em proposta/contrato por loja CRM."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        ok = skip = 0

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
                changed = False
                with conn.cursor() as cursor:
                    for table in TABLES:
                        if not table_exists(cursor, table):
                            continue
                        if not column_exists(cursor, table, COLUMN):
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {COLUMN} {DDL}")
                            self.stdout.write(f"{loja.slug}: coluna {COLUMN} adicionada em {table}")
                            changed = True
                if changed:
                    with contextlib.suppress(Exception):
                        call_command(
                            "migrate",
                            "crm_vendas",
                            "0060_canal_assinatura_vendedor",
                            database=db_name,
                            verbosity=0,
                        )
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{loja.slug}: {exc}"))
                skip += 1

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s) OK, {skip} pulada(s)."))
