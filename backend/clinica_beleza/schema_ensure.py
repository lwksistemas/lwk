"""
Utilitários compartilhados para comandos ensure_* (schemas multi-tenant).
"""
import logging
from typing import Callable, Iterable, Optional

from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

logger = logging.getLogger(__name__)

CONSULTA_TABLE = 'clinica_beleza_consultas'
PRODUTO_ESTOQUE_TABLE = 'clinica_beleza_produtoestoque'
CONSULTA_PRODUTO_TABLE = 'clinica_beleza_consultaprodutoutilizado'
MIGRATION_CONSULTA_PRODUTO = '0034_consulta_produto_numero_nota'
MIGRATION_RETORNO_GRATUITO = '0047_retorno_gratuito_agenda'


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


def ensure_consulta_produto_utilizado_table(cursor) -> bool:
    """
    Cria clinica_beleza_consultaprodutoutilizado se ausente no schema atual.
    Retorna True quando a tabela existe ou foi criada com sucesso.
    """
    if table_exists(cursor, CONSULTA_PRODUTO_TABLE):
        return True
    if not table_exists(cursor, CONSULTA_TABLE):
        logger.warning('ensure_consulta_produto: tabela %s ausente', CONSULTA_TABLE)
        return False
    if not table_exists(cursor, PRODUTO_ESTOQUE_TABLE):
        logger.warning('ensure_consulta_produto: tabela %s ausente', PRODUTO_ESTOQUE_TABLE)
        return False

    cursor.execute(f"""
        CREATE TABLE {CONSULTA_PRODUTO_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            quantidade NUMERIC(10, 2) NOT NULL,
            lote VARCHAR(50) NOT NULL DEFAULT '',
            validade DATE NULL,
            estoque_baixado BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consulta_id BIGINT NOT NULL
                REFERENCES {CONSULTA_TABLE}(id) ON DELETE CASCADE,
            produto_id BIGINT NOT NULL
                REFERENCES {PRODUTO_ESTOQUE_TABLE}(id) ON DELETE RESTRICT
        )
    """)
    cursor.execute(
        f'CREATE INDEX IF NOT EXISTS {CONSULTA_PRODUTO_TABLE}_loja_id_idx '
        f'ON {CONSULTA_PRODUTO_TABLE} (loja_id)'
    )
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'clinica_beleza', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'clinica_beleza' AND name = %s
        )
        """,
        [MIGRATION_CONSULTA_PRODUTO, MIGRATION_CONSULTA_PRODUTO],
    )
    return True


def ensure_retorno_gratuito_tables(cursor) -> bool:
    """Cria tabelas/colunas de retorno gratuito no schema atual (IF NOT EXISTS)."""
    if not table_exists(cursor, 'clinica_beleza_appointment'):
        logger.warning('ensure_retorno: tabela clinica_beleza_appointment ausente')
        return False

    if not table_exists(cursor, 'clinica_beleza_agenda_retorno_config'):
        cursor.execute("""
            CREATE TABLE clinica_beleza_agenda_retorno_config (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                retorno_procedimento_ativo BOOLEAN NOT NULL DEFAULT FALSE,
                retorno_consulta_ativo BOOLEAN NOT NULL DEFAULT FALSE,
                dias_retorno_consulta INTEGER NOT NULL DEFAULT 30
                    CHECK (dias_retorno_consulta >= 0),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS clinica_beleza_agenda_retorno_config_loja_id_idx '
            'ON clinica_beleza_agenda_retorno_config (loja_id)'
        )

    if not table_exists(cursor, 'clinica_beleza_retorno_procedimento_regra'):
        if not table_exists(cursor, 'clinica_beleza_procedure'):
            logger.warning('ensure_retorno: tabela clinica_beleza_procedure ausente')
            return False
        cursor.execute("""
            CREATE TABLE clinica_beleza_retorno_procedimento_regra (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                dias_retorno INTEGER NOT NULL CHECK (dias_retorno >= 1),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                procedure_id BIGINT NOT NULL
                    REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
                CONSTRAINT uniq_retorno_procedimento_loja
                    UNIQUE (procedure_id, loja_id)
            )
        """)
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS clinica_beleza_retorno_procedimento_regra_loja_id_idx '
            'ON clinica_beleza_retorno_procedimento_regra (loja_id)'
        )

    if not column_exists(cursor, 'clinica_beleza_appointment', 'retorno_procedure_id'):
        if table_exists(cursor, 'clinica_beleza_procedure'):
            cursor.execute("""
                ALTER TABLE clinica_beleza_appointment
                ADD COLUMN retorno_procedure_id BIGINT NULL
                REFERENCES clinica_beleza_procedure(id) ON DELETE SET NULL
            """)

    if table_exists(cursor, CONSULTA_TABLE):
        if not column_exists(cursor, CONSULTA_TABLE, 'retorno_gratuito'):
            cursor.execute(
                f'ALTER TABLE {CONSULTA_TABLE} '
                'ADD COLUMN retorno_gratuito BOOLEAN NOT NULL DEFAULT FALSE'
            )
        if not column_exists(cursor, CONSULTA_TABLE, 'retorno_tipo'):
            cursor.execute(
                f'ALTER TABLE {CONSULTA_TABLE} '
                "ADD COLUMN retorno_tipo VARCHAR(20) NOT NULL DEFAULT ''"
            )

    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'clinica_beleza', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'clinica_beleza' AND name = %s
        )
        """,
        [MIGRATION_RETORNO_GRATUITO, MIGRATION_RETORNO_GRATUITO],
    )
    return True


def ensure_retorno_gratuito_for_tenant() -> bool:
    """Garante schema de retorno no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == 'default':
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_retorno_gratuito_tables(cursor)
    except Exception as exc:
        logger.exception('ensure_retorno_gratuito_for_tenant falhou: %s', exc)
        return False


def ensure_consulta_produto_utilizado_for_tenant() -> bool:
    """Garante a tabela no schema tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == 'default':
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_consulta_produto_utilizado_table(cursor)
    except Exception as exc:
        logger.exception('ensure_consulta_produto_for_tenant falhou: %s', exc)
        return False


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
