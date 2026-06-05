"""
Utilitários compartilhados para comandos ensure_* (schemas multi-tenant).
"""
from typing import Callable, Iterable, Optional

from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


def table_exists(cursor, table: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = %s LIMIT 1
        """,
        [table],
    )
    return cursor.fetchone() is not None


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def iter_lojas(slug_filter: str = '') -> Iterable[Loja]:
    slug = (slug_filter or '').strip().lower()
    lojas = Loja.objects.filter(is_active=True, database_created=True)
    for loja in lojas:
        if slug and slug not in (
            (loja.slug or '').lower(),
            (getattr(loja, 'atalho', None) or '').lower(),
        ):
            continue
        yield loja


def run_for_lojas(
    slug_filter: str,
    *,
    prerequisite_table: Optional[str] = None,
    apply_fn: Callable,
) -> tuple[int, int]:
    """
    Executa apply_fn(cursor, loja) em cada loja ativa.
    Retorna (ok_count, skip_count).
    """
    ok = skip = 0
    for loja in iter_lojas(slug_filter):
        db_name = loja.database_name
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            skip += 1
            continue
        try:
            conn = connections[db_name]
            with conn.cursor() as cursor:
                if prerequisite_table and not table_exists(cursor, prerequisite_table):
                    skip += 1
                    continue
                apply_fn(cursor, loja)
            ok += 1
        except Exception:
            skip += 1
            raise
        finally:
            try:
                connections[db_name].close()
            except Exception:
                pass
    return ok, skip
