"""SQL idempotente para histórico de negociação CRM (migration 0069) em tenants."""
from clinica_beleza.schema_ensure import column_exists, table_exists

TABLE_OPORTUNIDADE = 'crm_vendas_oportunidade'
TABLE_NOTA = 'crm_vendas_oportunidade_nota'
MIGRATION_NAME = '0069_oportunidade_negociacao_historico'


def negociacao_historico_schema_missing(cursor) -> bool:
    if not column_exists(cursor, TABLE_OPORTUNIDADE, 'motivo_perda'):
        return True
    if not column_exists(cursor, TABLE_OPORTUNIDADE, 'feedback_pos_venda'):
        return True
    return not table_exists(cursor, TABLE_NOTA)


def ensure_negociacao_historico_schema(cursor, schema_name: str) -> bool:
    """Aplica colunas e tabela da migration 0069 quando ausentes no tenant."""
    cursor.execute(f'SET search_path TO "{schema_name}", public')

    if not negociacao_historico_schema_missing(cursor):
        return False

    if not column_exists(cursor, TABLE_OPORTUNIDADE, 'motivo_perda'):
        cursor.execute(
            f"""
            ALTER TABLE "{schema_name}".{TABLE_OPORTUNIDADE}
            ADD COLUMN IF NOT EXISTS motivo_perda TEXT NOT NULL DEFAULT ''
            """
        )
    if not column_exists(cursor, TABLE_OPORTUNIDADE, 'feedback_pos_venda'):
        cursor.execute(
            f"""
            ALTER TABLE "{schema_name}".{TABLE_OPORTUNIDADE}
            ADD COLUMN IF NOT EXISTS feedback_pos_venda TEXT NOT NULL DEFAULT ''
            """
        )

    if not table_exists(cursor, TABLE_NOTA):
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".{TABLE_NOTA} (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                tipo VARCHAR(30) NOT NULL DEFAULT 'resposta_cliente',
                texto TEXT NOT NULL,
                autor_nome VARCHAR(255) NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                oportunidade_id BIGINT NOT NULL
                    REFERENCES "{schema_name}".{TABLE_OPORTUNIDADE}(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS crm_opor_nota_loja_op_idx
            ON "{schema_name}".{TABLE_NOTA} (loja_id, oportunidade_id)
            """
        )
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS crm_opor_nota_loja_dt_idx
            ON "{schema_name}".{TABLE_NOTA} (loja_id, created_at)
            """
        )

    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'crm_vendas', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'crm_vendas' AND name = %s
        )
        """,
        [MIGRATION_NAME, MIGRATION_NAME],
    )
    return True
