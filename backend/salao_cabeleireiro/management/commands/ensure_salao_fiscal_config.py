"""Garante tabelas fiscais do salão (db_table fora do prefixo salao_cabeleireiro_).

Uso:
    python manage.py ensure_salao_fiscal_config
    python manage.py ensure_salao_fiscal_config --slug salao-teste
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from core.schema_checks import table_exists
from salao_cabeleireiro.schema_ensure import (
    NFCE_CONFIG_TABLE,
    NFSE_CONFIG_TABLE,
    ensure_salao_fiscal_tables,
    queryset_lojas_salao,
)


class Command(BaseCommand):
    help = "Cria salao_nfse_config e salao_nfce_config (IF NOT EXISTS) nos schemas do salão."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        ok = skip = 0

        for loja in queryset_lojas_salao():
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f"  SKIP {loja.slug}: banco não configurado"))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    before = (
                        table_exists(cursor, NFSE_CONFIG_TABLE)
                        and table_exists(cursor, NFCE_CONFIG_TABLE)
                    )
                    created = ensure_salao_fiscal_tables(cursor)
                    after = (
                        table_exists(cursor, NFSE_CONFIG_TABLE)
                        and table_exists(cursor, NFCE_CONFIG_TABLE)
                    )

                if not created:
                    skip += 1
                    self.stdout.write(self.style.WARNING(
                        f"  SKIP {loja.slug} ({db_name}): não foi possível criar tabelas fiscais",
                    ))
                    continue

                ok += 1
                if not before and after:
                    self.stdout.write(self.style.SUCCESS(
                        f"  OK {loja.slug} ({loja.nome}) db={db_name}: tabelas fiscais criadas",
                    ))
                else:
                    self.stdout.write(f"  OK (já existe) {loja.slug} ({loja.nome})")
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"  ERRO {loja.slug}: {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok} loja(s), {skip} ignorada(s)/erro."))
