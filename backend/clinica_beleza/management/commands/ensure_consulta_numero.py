"""Preenche numero sequencial (001, 002…) em clinica_beleza_consultas.

A migration 0062 só numerava linhas com loja_id preenchido; em várias lojas
loja_id estava NULL e o Nº ficou vazio na listagem.

Uso:
    python manage.py ensure_consulta_numero
    python manage.py ensure_consulta_numero --slug vida
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.catalogo_service import lojas_clinica_beleza_com_schema
from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config


class Command(BaseCommand):
    help = "Garante coluna numero e preenche sequência nas consultas da loja."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho/CNPJ")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = lojas_clinica_beleza_com_schema(apenas_ativas=True)
        ok = skip = filled = 0

        for loja in lojas:
            cnpj_digits = "".join(ch for ch in (getattr(loja, "cnpj", None) or "") if ch.isdigit())
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
                cnpj_digits,
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
                    if not table_exists(cursor, "clinica_beleza_consultas"):
                        skip += 1
                        continue
                    if not column_exists(cursor, "clinica_beleza_consultas", "numero"):
                        cursor.execute(
                            """
                            ALTER TABLE clinica_beleza_consultas
                            ADD COLUMN numero INTEGER NULL
                            """,
                        )
                    # Preenche loja_id nulo + numera por id (001, 002…).
                    cursor.execute(
                        """
                        WITH ordered AS (
                            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
                            FROM clinica_beleza_consultas
                        )
                        UPDATE clinica_beleza_consultas c
                        SET
                            numero = ordered.rn,
                            loja_id = COALESCE(c.loja_id, %s)
                        FROM ordered
                        WHERE c.id = ordered.id
                        """,
                        [loja.id],
                    )
                    n = cursor.rowcount or 0
                    cursor.execute(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint
                                WHERE conname = 'uniq_consulta_numero_por_loja'
                            ) THEN
                                ALTER TABLE clinica_beleza_consultas
                                ADD CONSTRAINT uniq_consulta_numero_por_loja
                                UNIQUE (loja_id, numero);
                            END IF;
                        EXCEPTION WHEN others THEN
                            NULL;
                        END $$;
                        """,
                    )
                ok += 1
                filled += n
                self.stdout.write(self.style.SUCCESS(
                    f"OK loja={loja.id} ({loja.nome}) db={db_name}: {n} consulta(s) numerada(s)",
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"ERRO loja={loja.id} ({loja.nome}): {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(
            f"Concluído: {ok} loja(s), {filled} linha(s) atualizada(s), {skip} ignorada(s).",
        ))
