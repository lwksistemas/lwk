"""Utilitários compartilhados para comandos ensure_* (schemas multi-tenant).
"""
import logging
from collections.abc import Callable, Iterable
from contextlib import suppress

from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

logger = logging.getLogger(__name__)

CONSULTA_TABLE = "clinica_beleza_consultas"
PRODUTO_ESTOQUE_TABLE = "clinica_beleza_produtoestoque"
CONSULTA_PRODUTO_TABLE = "clinica_beleza_consultaprodutoutilizado"
MIGRATION_CONSULTA_PRODUTO = "0034_consulta_produto_numero_nota"
MIGRATION_RETORNO_GRATUITO = "0047_retorno_gratuito_agenda"
MIGRATION_PATIENT_FOTO_URL = "0048_patient_foto_url"
MIGRATION_PATIENT_ANAMNESE = "0019_consulta_anamnese_evolucao"
MIGRATION_ORCAMENTO = "0077_orcamento_consulta"
MIGRATION_ORCAMENTO_ITEM_LOJA = "0078_orcamento_item_loja_id"
MIGRATION_PATIENT_PRAZO = "0081_patient_prazo_pagamento"
MIGRATION_PAYMENT_VENCIMENTO = "0082_payment_data_vencimento"
PATIENT_TABLE = "clinica_beleza_patient"
PAYMENT_TABLE = "clinica_beleza_payment"
PROFESSIONAL_TABLE = "clinica_beleza_professional"
PROCEDURE_TABLE = "clinica_beleza_procedure"
ANAMNESE_TABLE = "clinica_beleza_anamneses"
ORCAMENTO_CONSULTA_TABLE = "clinica_beleza_orcamento_consulta"
ORCAMENTO_ITEM_TABLE = "clinica_beleza_orcamento_item"


def _is_sqlite(cursor) -> bool:
    return getattr(cursor.db, "vendor", None) == "sqlite" or "sqlite" in str(cursor.connection).lower()


def table_exists(cursor, table: str) -> bool:
    if _is_sqlite(cursor):
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s LIMIT 1",
            [table],
        )
    else:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema() AND table_name = %s LIMIT 1
            """,
            [table],
        )
    return cursor.fetchone() is not None


def _record_clinica_migration(cursor, name: str) -> None:
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'clinica_beleza', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'clinica_beleza' AND name = %s
        )
        """,
        [name, name],
    )


def _fk_id_type(cursor, table: str) -> str:
    """INTEGER/BIGINT da PK da tabela pai — lojas antigas usam INTEGER."""
    if _is_sqlite(cursor):
        return "INTEGER"
    cursor.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = 'id'
        LIMIT 1
        """,
        [table],
    )
    row = cursor.fetchone()
    if row and str(row[0]).lower() == "bigint":
        return "BIGINT"
    return "INTEGER"


def column_exists(cursor, table: str, column: str) -> bool:
    if _is_sqlite(cursor):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
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
    """Cria clinica_beleza_consultaprodutoutilizado se ausente no schema atual.
    Retorna True quando a tabela existe ou foi criada com sucesso.
    """
    if table_exists(cursor, CONSULTA_PRODUTO_TABLE):
        return True
    if not table_exists(cursor, CONSULTA_TABLE):
        logger.warning("ensure_consulta_produto: tabela %s ausente", CONSULTA_TABLE)
        return False
    if not table_exists(cursor, PRODUTO_ESTOQUE_TABLE):
        logger.warning("ensure_consulta_produto: tabela %s ausente", PRODUTO_ESTOQUE_TABLE)
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
        f"CREATE INDEX IF NOT EXISTS {CONSULTA_PRODUTO_TABLE}_loja_id_idx "
        f"ON {CONSULTA_PRODUTO_TABLE} (loja_id)",
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
    if not table_exists(cursor, "clinica_beleza_appointment"):
        logger.warning("ensure_retorno: tabela clinica_beleza_appointment ausente")
        return False

    if not table_exists(cursor, "clinica_beleza_agenda_retorno_config"):
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
            "CREATE INDEX IF NOT EXISTS clinica_beleza_agenda_retorno_config_loja_id_idx "
            "ON clinica_beleza_agenda_retorno_config (loja_id)",
        )

    if not table_exists(cursor, "clinica_beleza_retorno_procedimento_regra"):
        if not table_exists(cursor, "clinica_beleza_procedure"):
            logger.warning(
                "ensure_retorno: tabela clinica_beleza_procedure ausente — regras por procedimento omitidas",
            )
        else:
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
                "CREATE INDEX IF NOT EXISTS clinica_beleza_retorno_procedimento_regra_loja_id_idx "
                "ON clinica_beleza_retorno_procedimento_regra (loja_id)",
            )

    if (
        not column_exists(cursor, "clinica_beleza_appointment", "retorno_procedure_id")
        and table_exists(cursor, "clinica_beleza_procedure")
    ):
        cursor.execute("""
            ALTER TABLE clinica_beleza_appointment
            ADD COLUMN retorno_procedure_id BIGINT NULL
            REFERENCES clinica_beleza_procedure(id) ON DELETE SET NULL
        """)

    if table_exists(cursor, CONSULTA_TABLE):
        if not column_exists(cursor, CONSULTA_TABLE, "retorno_gratuito"):
            cursor.execute(
                f"ALTER TABLE {CONSULTA_TABLE} "
                "ADD COLUMN retorno_gratuito BOOLEAN NOT NULL DEFAULT FALSE",
            )
        if not column_exists(cursor, CONSULTA_TABLE, "retorno_tipo"):
            cursor.execute(
                f"ALTER TABLE {CONSULTA_TABLE} "
                "ADD COLUMN retorno_tipo VARCHAR(20) NOT NULL DEFAULT ''",
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


def ensure_patient_foto_url_column(cursor) -> bool:
    """Adiciona foto_url em clinica_beleza_patient se ausente no schema atual."""
    if not table_exists(cursor, PATIENT_TABLE):
        logger.warning("ensure_patient_foto_url: tabela %s ausente", PATIENT_TABLE)
        return False
    if not column_exists(cursor, PATIENT_TABLE, "foto_url"):
        cursor.execute(
            f"ALTER TABLE {PATIENT_TABLE} ADD COLUMN foto_url VARCHAR(500) NOT NULL DEFAULT ''",
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
        [MIGRATION_PATIENT_FOTO_URL, MIGRATION_PATIENT_FOTO_URL],
    )
    return True


def ensure_patient_prazo_columns(cursor) -> bool:
    """Adiciona colunas de política de prazo de pagamento em clinica_beleza_patient."""
    if not table_exists(cursor, PATIENT_TABLE):
        logger.warning("ensure_patient_prazo: tabela %s ausente", PATIENT_TABLE)
        return False
    if not column_exists(cursor, PATIENT_TABLE, "prazo_pagamento_modo"):
        cursor.execute(
            f"ALTER TABLE {PATIENT_TABLE} ADD COLUMN prazo_pagamento_modo VARCHAR(20) NOT NULL DEFAULT ''",
        )
    if not column_exists(cursor, PATIENT_TABLE, "prazo_pagamento_dias"):
        cursor.execute(
            f"ALTER TABLE {PATIENT_TABLE} ADD COLUMN prazo_pagamento_dias SMALLINT NULL",
        )
    if not column_exists(cursor, PATIENT_TABLE, "prazo_pagamento_dia_mes"):
        cursor.execute(
            f"ALTER TABLE {PATIENT_TABLE} ADD COLUMN prazo_pagamento_dia_mes SMALLINT NULL",
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
        [MIGRATION_PATIENT_PRAZO, MIGRATION_PATIENT_PRAZO],
    )
    return True


def ensure_payment_vencimento_column(cursor) -> bool:
    """Adiciona coluna data_vencimento em clinica_beleza_payment (contas a receber a prazo)."""
    if not table_exists(cursor, PAYMENT_TABLE):
        logger.warning("ensure_payment_vencimento: tabela %s ausente", PAYMENT_TABLE)
        return False
    if not column_exists(cursor, PAYMENT_TABLE, "data_vencimento"):
        cursor.execute(
            f"ALTER TABLE {PAYMENT_TABLE} ADD COLUMN data_vencimento DATE NULL",
        )
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS cb_payment_venc_idx "
        f"ON {PAYMENT_TABLE} (loja_id, status, data_vencimento)",
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
        [MIGRATION_PAYMENT_VENCIMENTO, MIGRATION_PAYMENT_VENCIMENTO],
    )
    return True


def ensure_patient_anamnese_table(cursor) -> bool:
    """Cria clinica_beleza_anamneses se ausente no schema atual."""
    if table_exists(cursor, ANAMNESE_TABLE):
        return True
    if not table_exists(cursor, PATIENT_TABLE):
        logger.warning("ensure_patient_anamnese: tabela %s ausente", PATIENT_TABLE)
        return False

    cursor.execute(f"""
        CREATE TABLE {ANAMNESE_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            queixa_principal TEXT NOT NULL DEFAULT '',
            historico_medico TEXT NOT NULL DEFAULT '',
            medicamentos_uso TEXT NOT NULL DEFAULT '',
            alergias TEXT NOT NULL DEFAULT '',
            condicoes_clinicas TEXT NOT NULL DEFAULT '',
            tipo_pele TEXT NOT NULL DEFAULT '',
            pressao_arterial TEXT NOT NULL DEFAULT '',
            peso NUMERIC(5, 2) NULL,
            altura NUMERIC(4, 2) NULL,
            observacoes TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            patient_id BIGINT NOT NULL UNIQUE REFERENCES {PATIENT_TABLE}(id) ON DELETE CASCADE
        )
    """)
    cursor.execute(
        """
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'clinica_beleza', %s, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations
            WHERE app = 'clinica_beleza' AND name = %s
        )
        """,
        [MIGRATION_PATIENT_ANAMNESE, MIGRATION_PATIENT_ANAMNESE],
    )
    return True


def _ensure_orcamento_item_loja_id(cursor) -> None:
    """ADD COLUMN + copia do pai. Nunca DROP/DELETE."""
    if not table_exists(cursor, ORCAMENTO_ITEM_TABLE):
        return
    if not column_exists(cursor, ORCAMENTO_ITEM_TABLE, "loja_id"):
        cursor.execute(f"ALTER TABLE {ORCAMENTO_ITEM_TABLE} ADD COLUMN loja_id INTEGER")
    if table_exists(cursor, ORCAMENTO_CONSULTA_TABLE):
        cursor.execute(f"""
            UPDATE {ORCAMENTO_ITEM_TABLE} AS i
            SET loja_id = o.loja_id
            FROM {ORCAMENTO_CONSULTA_TABLE} AS o
            WHERE i.orcamento_id = o.id
              AND i.loja_id IS NULL
        """)
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS {ORCAMENTO_ITEM_TABLE}_loja_id_idx "
        f"ON {ORCAMENTO_ITEM_TABLE} (loja_id)",
    )
    _record_clinica_migration(cursor, MIGRATION_ORCAMENTO_ITEM_LOJA)


def ensure_orcamento_tables(cursor) -> bool:
    """Cria tabelas de orçamento da consulta se ausentes no schema atual."""
    consulta_ok = table_exists(cursor, ORCAMENTO_CONSULTA_TABLE)
    item_ok = table_exists(cursor, ORCAMENTO_ITEM_TABLE)
    if consulta_ok and item_ok:
        _ensure_orcamento_item_loja_id(cursor)
        _record_clinica_migration(cursor, MIGRATION_ORCAMENTO)
        return True

    if not table_exists(cursor, CONSULTA_TABLE):
        logger.warning("ensure_orcamento: tabela %s ausente", CONSULTA_TABLE)
        return False
    if not table_exists(cursor, PATIENT_TABLE):
        logger.warning("ensure_orcamento: tabela %s ausente", PATIENT_TABLE)
        return False
    if not table_exists(cursor, PROFESSIONAL_TABLE):
        logger.warning("ensure_orcamento: tabela %s ausente", PROFESSIONAL_TABLE)
        return False
    if not table_exists(cursor, PROCEDURE_TABLE):
        logger.warning("ensure_orcamento: tabela %s ausente", PROCEDURE_TABLE)
        return False

    consulta_id_type = _fk_id_type(cursor, CONSULTA_TABLE)
    patient_id_type = _fk_id_type(cursor, PATIENT_TABLE)
    professional_id_type = _fk_id_type(cursor, PROFESSIONAL_TABLE)
    procedure_id_type = _fk_id_type(cursor, PROCEDURE_TABLE)
    orcamento_pk_type = _fk_id_type(cursor, ORCAMENTO_CONSULTA_TABLE) if consulta_ok else "BIGINT"

    if not consulta_ok:
        cursor.execute(f"""
            CREATE TABLE {ORCAMENTO_CONSULTA_TABLE} (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                observacoes TEXT NOT NULL DEFAULT '',
                valor_total NUMERIC(10, 2) NOT NULL DEFAULT 0,
                validade_dias INTEGER NOT NULL DEFAULT 30,
                status VARCHAR(20) NOT NULL DEFAULT 'RASCUNHO',
                enviado_email BOOLEAN NOT NULL DEFAULT FALSE,
                enviado_whatsapp BOOLEAN NOT NULL DEFAULT FALSE,
                data_envio TIMESTAMPTZ NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                consulta_id {consulta_id_type} NOT NULL
                    REFERENCES {CONSULTA_TABLE}(id) ON DELETE CASCADE,
                patient_id {patient_id_type} NOT NULL
                    REFERENCES {PATIENT_TABLE}(id) ON DELETE CASCADE,
                professional_id {professional_id_type} NULL
                    REFERENCES {PROFESSIONAL_TABLE}(id) ON DELETE SET NULL
            )
        """)
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {ORCAMENTO_CONSULTA_TABLE}_loja_id_idx "
            f"ON {ORCAMENTO_CONSULTA_TABLE} (loja_id)",
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {ORCAMENTO_CONSULTA_TABLE}_consulta_id_idx "
            f"ON {ORCAMENTO_CONSULTA_TABLE} (consulta_id)",
        )
        orcamento_pk_type = "BIGINT"

    if not item_ok:
        cursor.execute(f"""
            CREATE TABLE {ORCAMENTO_ITEM_TABLE} (
                id BIGSERIAL PRIMARY KEY,
                nome_procedimento VARCHAR(200) NOT NULL,
                descricao_procedimento TEXT NOT NULL DEFAULT '',
                valor_original NUMERIC(10, 2) NOT NULL,
                valor_customizado NUMERIC(10, 2) NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 1,
                observacao_item TEXT NOT NULL DEFAULT '',
                orcamento_id {orcamento_pk_type} NOT NULL
                    REFERENCES {ORCAMENTO_CONSULTA_TABLE}(id) ON DELETE CASCADE,
                procedure_id {procedure_id_type} NULL
                    REFERENCES {PROCEDURE_TABLE}(id) ON DELETE SET NULL,
                loja_id INTEGER NOT NULL
            )
        """)
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {ORCAMENTO_ITEM_TABLE}_orcamento_id_idx "
            f"ON {ORCAMENTO_ITEM_TABLE} (orcamento_id)",
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {ORCAMENTO_ITEM_TABLE}_loja_id_idx "
            f"ON {ORCAMENTO_ITEM_TABLE} (loja_id)",
        )

    _ensure_orcamento_item_loja_id(cursor)
    _record_clinica_migration(cursor, MIGRATION_ORCAMENTO)
    return True


def ensure_patient_anamnese_for_tenant() -> bool:
    """Garante tabela de anamnese no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_patient_anamnese_table(cursor)
    except Exception as exc:
        logger.exception("ensure_patient_anamnese_for_tenant falhou: %s", exc)
        return False


def ensure_patient_foto_url_for_tenant() -> bool:
    """Garante coluna foto_url no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_patient_foto_url_column(cursor)
    except Exception as exc:
        logger.exception("ensure_patient_foto_url_for_tenant falhou: %s", exc)
        return False


def ensure_patient_prazo_for_tenant() -> bool:
    """Garante colunas de prazo de pagamento no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_patient_prazo_columns(cursor)
    except Exception as exc:
        logger.exception("ensure_patient_prazo_for_tenant falhou: %s", exc)
        return False


def ensure_payment_vencimento_for_tenant() -> bool:
    """Garante coluna data_vencimento no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_payment_vencimento_column(cursor)
    except Exception as exc:
        logger.exception("ensure_payment_vencimento_for_tenant falhou: %s", exc)
        return False


def ensure_retorno_gratuito_for_tenant() -> bool:
    """Garante schema de retorno no tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_retorno_gratuito_tables(cursor)
    except Exception as exc:
        logger.exception("ensure_retorno_gratuito_for_tenant falhou: %s", exc)
        return False


def ensure_consulta_produto_utilizado_for_tenant() -> bool:
    """Garante a tabela no schema tenant da requisição atual."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    if not tenant_db or tenant_db == "default":
        return True
    try:
        conn = connections[tenant_db]
        with conn.cursor() as cursor:
            return ensure_consulta_produto_utilizado_table(cursor)
    except Exception as exc:
        logger.exception("ensure_consulta_produto_for_tenant falhou: %s", exc)
        return False


def queryset_lojas_clinica_beleza():
    """Só lojas cujo tipo usa o app clinica_beleza — não Felix/CRM."""
    from superadmin.services.database_schema_service import TIPO_LOJA_EXTRA_APPS

    slugs = [k for k, apps in TIPO_LOJA_EXTRA_APPS.items() if "clinica_beleza" in apps]
    return Loja.objects.using("default").filter(
        is_active=True,
        database_created=True,
        tipo_loja__slug__in=slugs,
    ).select_related("tipo_loja")


def iter_lojas(slug_filter: str = "") -> Iterable[Loja]:
    slug = (slug_filter or "").strip().lower()
    lojas = queryset_lojas_clinica_beleza()
    for loja in lojas:
        if slug and slug not in (
            (loja.slug or "").lower(),
            (getattr(loja, "atalho", None) or "").lower(),
        ):
            continue
        yield loja


def run_for_lojas(
    slug_filter: str,
    *,
    prerequisite_table: str | None = None,
    apply_fn: Callable,
) -> tuple[int, int]:
    """Executa apply_fn(cursor, loja) em cada loja ativa.
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
            with suppress(Exception):
                connections[db_name].close()
    return ok, skip
