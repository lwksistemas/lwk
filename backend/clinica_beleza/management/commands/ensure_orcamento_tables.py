"""Garante tabelas de orçamento da consulta nos schemas das lojas.

Uso:
    python manage.py ensure_orcamento_tables
    python manage.py ensure_orcamento_tables --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import (
    ORCAMENTO_CONSULTA_TABLE,
    ensure_orcamento_tables,
    queryset_lojas_clinica_beleza,
    table_exists,
)
from core.db_config import ensure_loja_database_config


class Command(BaseCommand):
    help = "Cria tabelas de orçamento da consulta (IF NOT EXISTS) nos schemas das clínicas."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = queryset_lojas_clinica_beleza()
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
                    before = table_exists(cursor, ORCAMENTO_CONSULTA_TABLE)
                    created = ensure_orcamento_tables(cursor)
                    after = table_exists(cursor, ORCAMENTO_CONSULTA_TABLE)

                if not created:
                    skip += 1
                    self.stdout.write(self.style.WARNING(
                        f"  SKIP {loja.slug} ({db_name}): schema da clínica incompleto",
                    ))
                    continue

                ok += 1
                if not before and after:
                    self.stdout.write(self.style.SUCCESS(
                        f"  OK {loja.slug} ({loja.nome}) db={db_name}: orçamento criado",
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
