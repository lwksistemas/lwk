"""SQL idempotente para tabelas financeiro CRM (0064/0065) em tenants."""
from clinica_beleza.schema_ensure import table_exists

TABLE_GRUPO = "crm_financeiro_grupo"
TABLE_LANCAMENTO = "crm_financeiro_lancamento"
TABLE_RECORRENCIA = "crm_financeiro_recorrencia"


def aplicar_financeiro_base_sql(cursor, schema_name: str) -> bool:
    """Cria grupo + lançamento (migration 0064) sem migrate."""
    cursor.execute(f'SET search_path TO "{schema_name}", public')

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema_name}".{TABLE_GRUPO} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(100) NOT NULL,
            tipo VARCHAR(10) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            ordem SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema_name}".{TABLE_LANCAMENTO} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            tipo VARCHAR(10) NOT NULL,
            origem VARCHAR(20) NOT NULL DEFAULT 'manual',
            descricao VARCHAR(200) NOT NULL,
            valor NUMERIC(12, 2) NOT NULL,
            status VARCHAR(12) NOT NULL DEFAULT 'pendente',
            data_vencimento DATE NOT NULL,
            data_pagamento DATE NULL,
            observacoes TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            grupo_id BIGINT NULL REFERENCES "{schema_name}".{TABLE_GRUPO}(id) ON DELETE SET NULL,
            oportunidade_id BIGINT NULL UNIQUE
                REFERENCES "{schema_name}".crm_vendas_oportunidade(id) ON DELETE SET NULL,
            vendedor_id BIGINT NOT NULL
                REFERENCES "{schema_name}".crm_vendas_vendedor(id) ON DELETE CASCADE
        )
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_bf6f65_idx
        ON "{schema_name}".{TABLE_GRUPO} (loja_id, tipo, is_active)
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_6d486c_idx
        ON "{schema_name}".{TABLE_LANCAMENTO} (loja_id, tipo, status)
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_952ff3_idx
        ON "{schema_name}".{TABLE_LANCAMENTO} (loja_id, vendedor_id, tipo)
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_7ac72e_idx
        ON "{schema_name}".{TABLE_LANCAMENTO} (loja_id, data_vencimento)
        """,
    )
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'crm_vendas', '0064_financeiro_crm', NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'crm_vendas' AND name = '0064_financeiro_crm'
        )
        """,
    )
    return table_exists(cursor, TABLE_GRUPO) and table_exists(cursor, TABLE_LANCAMENTO)


def aplicar_recorrencia_sql(cursor, schema_name: str) -> bool:
    """Cria recorrência + coluna em lançamento (migration 0065) sem migrate."""
    cursor.execute(f'SET search_path TO "{schema_name}", public')
    if not table_exists(cursor, TABLE_GRUPO) or not table_exists(cursor, TABLE_LANCAMENTO):
        return False

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema_name}".{TABLE_RECORRENCIA} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            tipo VARCHAR(10) NOT NULL,
            descricao VARCHAR(200) NOT NULL,
            valor NUMERIC(12, 2) NOT NULL,
            frequencia VARCHAR(12) NOT NULL DEFAULT 'mensal',
            proximo_vencimento DATE NOT NULL,
            data_fim DATE NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            observacoes TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            grupo_id BIGINT NULL REFERENCES "{schema_name}".{TABLE_GRUPO}(id) ON DELETE SET NULL,
            vendedor_id BIGINT NOT NULL REFERENCES "{schema_name}".crm_vendas_vendedor(id) ON DELETE CASCADE
        )
        """,
    )
    cursor.execute(
        f"""
        ALTER TABLE "{schema_name}".{TABLE_LANCAMENTO}
        ADD COLUMN IF NOT EXISTS recorrencia_id BIGINT NULL
        REFERENCES "{schema_name}".{TABLE_RECORRENCIA}(id) ON DELETE SET NULL
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_recorr_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id, is_active, proximo_vencimento)
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS crm_finance_loja_id_rec_v_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id, vendedor_id, tipo)
        """,
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {TABLE_RECORRENCIA}_loja_id_idx
        ON "{schema_name}".{TABLE_RECORRENCIA} (loja_id)
        """,
    )
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'crm_vendas', '0065_financeiro_recorrencia', NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'crm_vendas' AND name = '0065_financeiro_recorrencia'
        )
        """,
    )
    return table_exists(cursor, TABLE_RECORRENCIA)


def ensure_financeiro_tabelas(cursor, schema_name: str) -> bool:
    """Garante as 3 tabelas financeiro no schema do tenant."""
    if not aplicar_financeiro_base_sql(cursor, schema_name):
        return False
    return aplicar_recorrencia_sql(cursor, schema_name)
