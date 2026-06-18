"""Garantias de schema CRM (colunas críticas em tenants legados)."""
from __future__ import annotations

import logging

from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config

logger = logging.getLogger(__name__)

TABLE = 'crm_vendas_assinatura_digital'
COLUMN = 'link_enviado_em'
DDL = 'TIMESTAMPTZ NULL'


def ensure_assinatura_link_enviado_em_coluna(tenant_db: str | None) -> None:
    """Adiciona link_enviado_em se ausente (idempotente, best-effort)."""
    if not tenant_db or tenant_db == 'default':
        return
    if not ensure_loja_database_config(tenant_db, conn_max_age=0):
        return
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            if not table_exists(cursor, TABLE):
                return
            if column_exists(cursor, TABLE, COLUMN):
                return
            cursor.execute(f'ALTER TABLE {TABLE} ADD COLUMN {COLUMN} {DDL}')
        conn.commit()
        logger.info('Coluna %s adicionada em %s (tenant=%s)', COLUMN, TABLE, tenant_db)
    except Exception as exc:
        logger.warning('ensure_assinatura_link_enviado_em_coluna(%s): %s', tenant_db, exc)
