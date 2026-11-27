"""Ensure DDL do salão — tabelas com db_table fora do prefixo salao_cabeleireiro_."""
from __future__ import annotations

import logging

from core.schema_checks import table_exists
from superadmin.tenant_deploy import queryset_lojas_do_app

logger = logging.getLogger(__name__)

NFSE_CONFIG_TABLE = "salao_nfse_config"
NFCE_CONFIG_TABLE = "salao_nfce_config"
MIGRATION_FISCAL = "0005_fiscal_config"

SQL_NFSE = f"""
CREATE TABLE IF NOT EXISTS {NFSE_CONFIG_TABLE} (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    provedor_nf VARCHAR(20) NOT NULL DEFAULT 'asaas',
    issnet_usuario VARCHAR(100) NOT NULL DEFAULT '',
    issnet_senha VARCHAR(500) NOT NULL DEFAULT '',
    issnet_certificado BYTEA NULL,
    issnet_certificado_nome VARCHAR(255) NOT NULL DEFAULT '',
    issnet_senha_certificado VARCHAR(500) NOT NULL DEFAULT '',
    issnet_ambiente_homologacao BOOLEAN NOT NULL DEFAULT FALSE,
    inscricao_municipal VARCHAR(20) NOT NULL DEFAULT '',
    codigo_cnae VARCHAR(20) NOT NULL DEFAULT '',
    optante_simples_nacional BOOLEAN NOT NULL DEFAULT TRUE,
    regime_especial_tributacao VARCHAR(2) NOT NULL DEFAULT '0',
    incentivador_cultural BOOLEAN NOT NULL DEFAULT FALSE,
    item_lista_servico VARCHAR(10) NOT NULL DEFAULT '',
    codigo_nbs VARCHAR(20) NOT NULL DEFAULT '',
    issnet_serie_rps VARCHAR(10) NOT NULL DEFAULT '',
    issnet_ultimo_rps_conhecido INTEGER NOT NULL DEFAULT 0,
    issnet_numero_lote INTEGER NOT NULL DEFAULT 0,
    codigo_servico_municipal VARCHAR(10) NOT NULL DEFAULT '0602',
    descricao_servico_padrao TEXT NOT NULL DEFAULT 'Serviços de cabeleireiro',
    aliquota_iss NUMERIC(5, 2) NOT NULL DEFAULT 2.0,
    emitir_nf_automaticamente BOOLEAN NOT NULL DEFAULT FALSE,
    issnet_usar_padrao_nacional BOOLEAN NOT NULL DEFAULT TRUE,
    codigo_tributacao_nacional VARCHAR(10) NOT NULL DEFAULT '',
    codigo_tributacao_municipal VARCHAR(10) NOT NULL DEFAULT '',
    nacional_codigo_municipio VARCHAR(7) NOT NULL DEFAULT '',
    indicador_operacao VARCHAR(2) NOT NULL DEFAULT '',
    cst_ibscbs VARCHAR(3) NOT NULL DEFAULT '',
    cclass_trib_ibscbs VARCHAR(6) NOT NULL DEFAULT '',
    p_tot_trib_sn NUMERIC(5, 2) NULL,
    asaas_api_key TEXT NOT NULL DEFAULT '',
    asaas_sandbox BOOLEAN NOT NULL DEFAULT FALSE,
    asaas_webhook_token TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

SQL_NFCE = f"""
CREATE TABLE IF NOT EXISTS {NFCE_CONFIG_TABLE} (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    habilitada BOOLEAN NOT NULL DEFAULT FALSE,
    regime VARCHAR(12) NOT NULL DEFAULT '',
    id_csc VARCHAR(6) NOT NULL DEFAULT '',
    csc VARCHAR(500) NOT NULL DEFAULT '',
    inscricao_estadual VARCHAR(20) NOT NULL DEFAULT '',
    serie SMALLINT NOT NULL DEFAULT 1 CHECK (serie >= 0),
    proximo_numero INTEGER NOT NULL DEFAULT 1 CHECK (proximo_numero >= 0),
    proximo_numero_teste INTEGER NOT NULL DEFAULT 1 CHECK (proximo_numero_teste >= 0),
    ambiente_homologacao BOOLEAN NOT NULL DEFAULT TRUE,
    ncm_padrao VARCHAR(8) NOT NULL DEFAULT '',
    codigo_municipio VARCHAR(7) NOT NULL DEFAULT '',
    aliquota_icms NUMERIC(5, 2) NOT NULL DEFAULT 18,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

SQL_NFSE_UNIQUE = f"""
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'salao_nfse_config_loja'
    ) THEN
        ALTER TABLE {NFSE_CONFIG_TABLE}
            ADD CONSTRAINT salao_nfse_config_loja UNIQUE (loja_id);
    END IF;
END $$
"""

SQL_NFCE_UNIQUE = f"""
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'salao_nfce_config_loja'
    ) THEN
        ALTER TABLE {NFCE_CONFIG_TABLE}
            ADD CONSTRAINT salao_nfce_config_loja UNIQUE (loja_id);
    END IF;
END $$
"""

SQL_NFSE_INDEX = f"""
CREATE INDEX IF NOT EXISTS salao_nfse_config_loja_id_idx
    ON {NFSE_CONFIG_TABLE} (loja_id)
"""

SQL_NFCE_INDEX = f"""
CREATE INDEX IF NOT EXISTS salao_nfce_config_loja_id_idx
    ON {NFCE_CONFIG_TABLE} (loja_id)
"""


def _record_salao_migration(cursor, name: str) -> None:
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'salao_cabeleireiro', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'salao_cabeleireiro' AND name = %s
        )
        """,
        [name, name],
    )


def ensure_salao_fiscal_tables(cursor) -> bool:
    """Cria salao_nfse_config e salao_nfce_config se ausentes no schema atual."""
    try:
        if not table_exists(cursor, NFSE_CONFIG_TABLE):
            cursor.execute(SQL_NFSE)
            cursor.execute(SQL_NFSE_INDEX)
            cursor.execute(SQL_NFSE_UNIQUE)
            logger.info("ensure_salao_fiscal: criada %s", NFSE_CONFIG_TABLE)
        if not table_exists(cursor, NFCE_CONFIG_TABLE):
            cursor.execute(SQL_NFCE)
            cursor.execute(SQL_NFCE_INDEX)
            cursor.execute(SQL_NFCE_UNIQUE)
            logger.info("ensure_salao_fiscal: criada %s", NFCE_CONFIG_TABLE)
        # Constraints podem faltar se a tabela veio de CREATE antigo sem UNIQUE.
        cursor.execute(SQL_NFSE_UNIQUE)
        cursor.execute(SQL_NFCE_UNIQUE)
        _record_salao_migration(cursor, MIGRATION_FISCAL)
        return table_exists(cursor, NFSE_CONFIG_TABLE) and table_exists(cursor, NFCE_CONFIG_TABLE)
    except Exception:
        logger.exception("ensure_salao_fiscal: falha ao criar tabelas fiscais")
        return False


def queryset_lojas_salao():
    return queryset_lojas_do_app("salao_cabeleireiro")
