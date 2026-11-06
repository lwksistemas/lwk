"""Preenche numero só nas consultas que ainda não têm.

Não reordena número já gravado. Consulta apagada deixa o buraco: a próxima
continua a partir do maior número existente, como o save() do model.

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


# Só linhas com numero vazio. O máximo existente fica de fora do ROW_NUMBER,
# senão um deploy torna a sequência densa e troca número já impresso na tela.
SQL_NUMERAR_SEM_NUMERO = """
WITH base AS (
    SELECT COALESCE(MAX(numero), 0) AS max_numero
    FROM clinica_beleza_consultas
    WHERE numero IS NOT NULL
),
faltantes AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
    FROM clinica_beleza_consultas
    WHERE numero IS NULL
)
UPDATE clinica_beleza_consultas c
SET
    numero = base.max_numero + faltantes.rn,
    loja_id = COALESCE(c.loja_id, %s)
FROM faltantes, base
WHERE c.id = faltantes.id
"""


class Command(BaseCommand):
    help = "Preenche numero apenas nas consultas que ainda não têm."

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
                    cursor.execute(SQL_NUMERAR_SEM_NUMERO, [loja.id])
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
                    f"OK loja={loja.id} ({loja.nome}) db={db_name}: {n} consulta(s) sem número preenchida(s)",
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
