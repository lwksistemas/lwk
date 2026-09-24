"""Garante tabelas do protocolo comercial (migration 0084) nos schemas das lojas."""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import ensure_protocolo_comercial, queryset_lojas_clinica_beleza, table_exists
from core.db_config import ensure_loja_database_config


class Command(BaseCommand):
    help = "Cria colunas e tabelas do protocolo comercial (IF NOT EXISTS). Não apaga dados."

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
                    if not table_exists(cursor, "clinica_beleza_protocolos"):
                        skip += 1
                        continue
                    antes = table_exists(cursor, "clinica_beleza_protocolo_contrato")
                    ensure_protocolo_comercial(cursor)
                    depois = table_exists(cursor, "clinica_beleza_protocolo_contrato")
                if not antes and depois:
                    ok += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"OK loja={loja.id} ({loja.nome}) db={db_name}: protocolo comercial criado",
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
