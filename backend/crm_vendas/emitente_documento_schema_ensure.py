"""SQL idempotente para colunas emitente_* em proposta/contrato (migration 0068)."""
from clinica_beleza.schema_ensure import column_exists, table_exists

TABLE_PROPOSTA = 'crm_vendas_proposta'
TABLE_CONTRATO = 'crm_vendas_contrato'
MIGRATION_NAME = '0068_emitente_documento_snapshot'

EMITENTE_COLUMNS = (
    ('emitente_nome', "VARCHAR(255) NOT NULL DEFAULT ''"),
    ('emitente_endereco', "VARCHAR(500) NOT NULL DEFAULT ''"),
    ('emitente_cpf_cnpj', "VARCHAR(18) NOT NULL DEFAULT ''"),
    ('emitente_responsavel', "VARCHAR(255) NOT NULL DEFAULT ''"),
    ('emitente_email', "VARCHAR(254) NOT NULL DEFAULT ''"),
)


def ensure_emitente_documento_columns(cursor, schema_name: str) -> bool:
    """Adiciona colunas emitente_* se faltarem. Retorna True se alterou algo."""
    cursor.execute(f'SET search_path TO "{schema_name}", public')
    changed = False
    for table in (TABLE_PROPOSTA, TABLE_CONTRATO):
        if not table_exists(cursor, table):
            continue
        for col, typedef in EMITENTE_COLUMNS:
            if column_exists(cursor, table, col):
                continue
            cursor.execute(f'ALTER TABLE "{schema_name}".{table} ADD COLUMN {col} {typedef}')
            changed = True
    if changed:
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
    return changed


def emitente_columns_missing(cursor) -> bool:
    """True se proposta existe mas falta emitente_nome."""
    if not table_exists(cursor, TABLE_PROPOSTA):
        return False
    return not column_exists(cursor, TABLE_PROPOSTA, 'emitente_nome')
