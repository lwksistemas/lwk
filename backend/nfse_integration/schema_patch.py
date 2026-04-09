"""
Garante colunas da migration 0002_nfse_asaas_ids no schema do tenant (PostgreSQL).

Em ambientes multi-tenant, ``migrate`` no banco da loja pode ficar defasado; o ADD COLUMN
IF NOT EXISTS é seguro e alinha a tabela ao modelo NFSe.
"""
import logging

from django.db import connections
from django.utils import timezone

logger = logging.getLogger(__name__)


def patch_nfse_asaas_columns_if_missing(db_name: str) -> None:
    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError(f'Não foi possível configurar o banco {db_name}')

    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE nfse_integration_nfse
            ADD COLUMN IF NOT EXISTS asaas_invoice_id VARCHAR(40) NOT NULL DEFAULT '';
            """
        )
        cursor.execute(
            """
            ALTER TABLE nfse_integration_nfse
            ADD COLUMN IF NOT EXISTS asaas_payment_id VARCHAR(40) NOT NULL DEFAULT '';
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS nfse_loja_asaas_inv_idx
            ON nfse_integration_nfse (loja_id, asaas_invoice_id);
            """
        )
        cursor.execute(
            """
            INSERT INTO django_migrations (app, name, applied)
            SELECT %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM django_migrations
                WHERE app = %s AND name = %s
            );
            """,
            [
                'nfse_integration',
                '0002_nfse_asaas_ids',
                timezone.now(),
                'nfse_integration',
                '0002_nfse_asaas_ids',
            ],
        )

    logger.info('NFSe: colunas asaas_invoice_id/asaas_payment_id aplicadas em %s', db_name)
