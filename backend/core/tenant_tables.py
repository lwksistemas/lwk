"""Verifica existência de tabelas no schema tenant de uma loja (cron / workers)."""
from __future__ import annotations

import logging

from django.db import connections

from clinica_beleza.schema_ensure import table_exists

logger = logging.getLogger(__name__)


def tenant_table_exists(db_name: str, table_name: str) -> bool:
    """True se a tabela existe no schema PostgreSQL da loja."""
    if not db_name or db_name == "default":
        return False
    schema = db_name.replace("-", "_")
    try:
        conn = connections[db_name]
        with conn.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}", public')
            return table_exists(cursor, table_name)
    except Exception as exc:
        logger.debug("tenant_table_exists(%s, %s): %s", db_name, table_name, exc)
        return False
