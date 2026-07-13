"""Serviço para configurar/recuperar schema do CRM.
Usado por: fix_loja_crm (command), auto-recovery nas views.

Deve aplicar os mesmos apps que DatabaseSchemaService na criação da loja
(inclui nfse_integration para lojas CRM — NFS-e no schema isolado).
"""
import contextlib
import logging
import os

from django.core.management import call_command
from django.db import connection, connections

from superadmin.services.database_schema_service import (
    APPS_CRITICOS_MIGRACAO_CRM_VENDAS,
    get_apps_esperados_para_loja,
)

logger = logging.getLogger(__name__)


def configurar_schema_crm_loja(loja) -> bool:
    """Configura schema e tabelas CRM para uma loja.
    Cria schema se não existir, aplica migrations, adiciona colunas faltantes.

    Returns:
        True se configurado com sucesso, False caso contrário.

    """
    if not loja:
        return False

    db_name = loja.database_name
    schema_name = db_name.replace("-", "_")
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() or "crm-vendas"

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        logger.warning("configurar_schema_crm_loja: DATABASE_URL não configurada")
        return False

    try:
        # 1. Garantir que o banco está em settings.DATABASES
        from core.db_config import ensure_loja_database_config
        if ensure_loja_database_config(db_name, conn_max_age=0):
            logger.info(f"Banco '{db_name}' configurado em settings.DATABASES")

        # 2. Criar schema se não existir
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name],
            )
            if not cursor.fetchone():
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                logger.info(f"Schema '{schema_name}' criado")

        # 2b. Limpar migrations clinica_beleza órfãs/inconsistentes (bloqueiam migrate em lojas CRM)
        try:
            patch_clinica_beleza_migration_orphans(db_name, tipo_slug=tipo_slug)
        except Exception as patch_exc:
            logger.warning("configurar_schema_crm_loja: patch clinica migrations em %s: %s", db_name, patch_exc)

        # 2c. Ordem quebrada em django_migrations (0067 sem 0066 / 0068 sem 0067)
        try:
            patch_crm_migration_0066_if_orphan(db_name)
            patch_crm_migration_0067_if_orphan(db_name)
        except Exception as patch_exc:
            logger.warning("configurar_schema_crm_loja: patch migrations CRM em %s: %s", db_name, patch_exc)

        # 3. Aplicar migrations (mesma lista que criar loja: get_apps_esperados_para_loja)
        apps = get_apps_esperados_para_loja(loja)

        for app in apps:
            try:
                conn = connections[db_name]
                conn.ensure_connection()
                with conn.cursor() as cur:
                    cur.execute(f'SET search_path TO "{schema_name}", public')
                call_command("migrate", app, "--database", db_name, verbosity=0)
                logger.info(f"Migrations aplicadas: {app}")
            except Exception as e:
                if tipo_slug == "crm-vendas" and app in APPS_CRITICOS_MIGRACAO_CRM_VENDAS:
                    logger.error(f"Erro crítico ao aplicar migration {app}: {e}")
                    return False
                logger.warning(f"Erro ao aplicar migration {app}: {e}")

        # 3b. Fallback: migrate pode ter criado tabelas em public; mover para o schema
        from superadmin.services.database_schema_service import DatabaseSchemaService
        DatabaseSchemaService._mover_tabelas_public_para_schema(loja, schema_name, apps)

        # 4. Marcar database_created na loja
        from superadmin.models import Loja
        if not loja.database_created:
            Loja.objects.filter(pk=loja.pk).update(database_created=True)
            logger.info(f"Loja {loja.slug} marcada como database_created=True")

        # 5. Patches SQL idempotentes (colunas que migrations podem não ter aplicado em tenants legados)
        try:
            apply_crm_tenant_schema_patches(db_name)
        except Exception as patch_exc:
            logger.warning("configurar_schema_crm_loja: patches SQL em %s: %s", db_name, patch_exc)

        # 6. Fechar conexão para forçar nova conexão com schema correto no retry
        if db_name in connections:
            with contextlib.suppress(Exception):
                connections[db_name].close()

        return True
    except Exception as e:
        logger.exception("configurar_schema_crm_loja: %s", e)
        return False


def patch_crm_migration_0066_if_orphan(db_name: str) -> bool:
    """Corrige django_migrations quando 0067/0068 está aplicada sem 0066 (bloqueia migrate).
    Garante coluna config_acesso e marca 0066 como aplicada.
    """
    from clinica_beleza.schema_ensure import column_exists, table_exists
    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return False

    schema_name = db_name.replace("-", "_")
    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["crm_vendas", "0066_vendedor_config_acesso"],
        )
        if cursor.fetchone():
            return False

        # Só corrige se há migration posterior já registrada (cadeia quebrada)
        cursor.execute(
            """
            SELECT 1 FROM django_migrations
            WHERE app = %s AND name IN (%s, %s)
            LIMIT 1
            """,
            [
                "crm_vendas",
                "0067_lead_cpfcnpj_index_opor_prob_constraint",
                "0068_emitente_documento_snapshot",
            ],
        )
        if not cursor.fetchone():
            return False

        if table_exists(cursor, "crm_vendas_vendedor") and not column_exists(
            cursor, "crm_vendas_vendedor", "config_acesso",
        ):
            cursor.execute(
                "ALTER TABLE crm_vendas_vendedor "
                "ADD COLUMN config_acesso JSONB NOT NULL DEFAULT '{}'::jsonb",
            )

        cursor.execute(
            """
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('crm_vendas', '0066_vendedor_config_acesso', NOW())
            """,
        )
        logger.warning(
            "patch_crm_migration_0066_if_orphan: %s — registro 0066 inserido (cadeia órfã)",
            db_name,
        )
        return True


def patch_crm_migration_0067_if_orphan(db_name: str) -> bool:
    """Corrige django_migrations quando 0068 está aplicada sem 0067 (bloqueia migrate).
    0067 só adiciona índice + check constraint — seguro marcar como aplicada se 0068 já rodou.
    """
    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return False

    schema_name = db_name.replace("-", "_")
    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["crm_vendas", "0068_emitente_documento_snapshot"],
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["crm_vendas", "0067_lead_cpfcnpj_index_opor_prob_constraint"],
        )
        if cursor.fetchone():
            return False
        cursor.execute(
            """
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('crm_vendas', '0067_lead_cpfcnpj_index_opor_prob_constraint', NOW())
            """,
        )
        logger.warning(
            "patch_crm_migration_0067_if_orphan: %s — registro 0067 inserido (0068 órfã)",
            db_name,
        )
        return True


def apply_crm_tenant_schema_patches(db_name: str) -> None:
    """Aplica todos os patches SQL idempotentes do CRM no schema do tenant.
    Usar em provisionamento, release (ensure_*) e recovery — nunca no hot path de requests.
    """
    patch_clinica_beleza_migration_orphans(db_name)
    patch_crm_migration_0066_if_orphan(db_name)
    patch_crm_migration_0067_if_orphan(db_name)
    patch_crm_financeiro_tables_if_missing(db_name)
    patch_crm_emitente_documento_columns_if_missing(db_name)
    patch_crm_vendas_asaas_columns_if_missing(db_name)
    patch_crm_vendas_atividade_columns_if_missing(db_name)
    patch_crm_negociacao_historico_if_missing(db_name)


def patch_crm_negociacao_historico_if_missing(db_name: str) -> bool:
    """Colunas motivo_perda/feedback_pos_venda e tabela de notas (migration 0069)."""
    from core.db_config import ensure_loja_database_config
    from crm_vendas.negociacao_historico_schema_ensure import (
        ensure_negociacao_historico_schema,
        negociacao_historico_schema_missing,
    )

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return False

    schema_name = db_name.replace("-", "_")
    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        if not negociacao_historico_schema_missing(cursor):
            return False
        logger.warning(
            "patch_crm_negociacao_historico_if_missing: %s sem schema 0069 — aplicando SQL",
            db_name,
        )
        return ensure_negociacao_historico_schema(cursor, schema_name)


def patch_crm_emitente_documento_columns_if_missing(db_name: str) -> bool:
    """Adiciona colunas emitente_* quando migration 0068 não rodou no schema do tenant."""
    from core.db_config import ensure_loja_database_config
    from crm_vendas.emitente_documento_schema_ensure import (
        emitente_columns_missing,
        ensure_emitente_documento_columns,
    )

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return False

    schema_name = db_name.replace("-", "_")
    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        if not emitente_columns_missing(cursor):
            return False
        logger.warning(
            "patch_crm_emitente_documento_columns_if_missing: %s sem colunas emitente — aplicando SQL",
            db_name,
        )
        return ensure_emitente_documento_columns(cursor, schema_name)


def patch_crm_financeiro_tables_if_missing(db_name: str) -> bool:
    """Cria tabelas financeiro CRM quando migrations 0064/0065 estão marcadas mas tabelas não existem.
    """
    from clinica_beleza.schema_ensure import table_exists
    from core.db_config import ensure_loja_database_config
    from crm_vendas.financeiro_schema_ensure import (
        TABLE_LANCAMENTO,
        ensure_financeiro_tabelas,
    )

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return False

    schema_name = db_name.replace("-", "_")
    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')
        if table_exists(cursor, TABLE_LANCAMENTO):
            return False
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["crm_vendas", "0064_financeiro_crm"],
        )
        if not cursor.fetchone():
            return False
        logger.warning(
            "patch_crm_financeiro_tables_if_missing: %s tem migration 0064 sem tabelas — aplicando SQL",
            db_name,
        )
        return ensure_financeiro_tabelas(cursor, schema_name)


def patch_clinica_beleza_migration_orphans(db_name: str, *, tipo_slug: str | None = None) -> int:
    """Remove registros clinica_beleza órfãos ou corrige 0025 sem 0024 em django_migrations.
    Lojas CRM não devem ter histórico clinica_beleza (quebra migrate de qualquer app).
    Retorna quantidade de registros removidos ou 0 se apenas corrigiu ordem.
    """
    from clinica_beleza.schema_ensure import column_exists, table_exists
    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        return 0

    removed = 0
    conn = connections[db_name]
    with conn.cursor() as cursor:
        if (tipo_slug or "").strip() == "crm-vendas":
            cursor.execute("DELETE FROM django_migrations WHERE app = %s", ["clinica_beleza"])
            return cursor.rowcount

        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name LIKE 'clinica_beleza_%%'
            """,
        )
        clinica_tables = (cursor.fetchone() or [0])[0]

        if clinica_tables == 0:
            cursor.execute("DELETE FROM django_migrations WHERE app = %s", ["clinica_beleza"])
            removed = cursor.rowcount
            return removed

        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["clinica_beleza", "0025_memed_timbrado"],
        )
        has_0025 = cursor.fetchone() is not None
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["clinica_beleza", "0024_professional_nascimento_sexo"],
        )
        has_0024 = cursor.fetchone() is not None

        if has_0025 and not has_0024:
            if table_exists(cursor, "clinica_beleza_professional"):
                for coluna, tipo in (
                    ("data_nascimento", "DATE NULL"),
                    ("sexo", "VARCHAR(1) NULL"),
                ):
                    if not column_exists(cursor, "clinica_beleza_professional", coluna):
                        cursor.execute(
                            f"ALTER TABLE clinica_beleza_professional ADD COLUMN {coluna} {tipo}",
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
                ["0024_professional_nascimento_sexo", "0024_professional_nascimento_sexo"],
            )

    return removed


def patch_atividade_schema_on_column_error(exc: Exception, db_name: str | None) -> bool:
    """Recovery pontual quando ORM falha por coluna ausente em crm_vendas_atividade.
    Retorna True se um patch foi aplicado (caller pode repetir a operação).
    """
    from django.db.utils import OperationalError, ProgrammingError

    if not db_name or db_name == "default":
        return False
    if not isinstance(exc, (ProgrammingError, OperationalError)):
        return False
    err_txt = str(exc).lower()
    if "does not exist" not in err_txt and "column" not in err_txt:
        return False
    triggers = ("crm_vendas_atividade", "lembrete_whatsapp", "conta_id")
    if not any(t in err_txt for t in triggers):
        return False
    patch_crm_vendas_atividade_columns_if_missing(db_name)
    return True


def patch_crm_vendas_asaas_columns_if_missing(db_name: str) -> None:
    """Garante colunas das migrations 0045, 0046, 0047, 0049, 0056 no schema do tenant.
    Usa ADD COLUMN IF NOT EXISTS (seguro no PostgreSQL).
    """
    from django.db import connections
    from django.utils import timezone

    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError(f"Não foi possível configurar o banco {db_name}")

    conn = connections[db_name]
    with conn.cursor() as cursor:
        # Migration 0045: asaas_api_key, asaas_sandbox
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS asaas_api_key VARCHAR(255) NOT NULL DEFAULT '';",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS asaas_sandbox boolean NOT NULL DEFAULT false;",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS asaas_webhook_token text NOT NULL DEFAULT '';",
        )
        # Migration 0046: campos do Portal Emissor
        columns_0046 = [
            ("inscricao_municipal", "VARCHAR(20) NOT NULL DEFAULT ''"),
            ("codigo_cnae", "VARCHAR(20) NOT NULL DEFAULT ''"),
            ("optante_simples_nacional", "boolean NOT NULL DEFAULT true"),
            ("regime_especial_tributacao", "VARCHAR(2) NOT NULL DEFAULT '0'"),
            ("incentivador_cultural", "boolean NOT NULL DEFAULT false"),
            ("item_lista_servico", "VARCHAR(10) NOT NULL DEFAULT ''"),
            ("codigo_nbs", "VARCHAR(20) NOT NULL DEFAULT ''"),
            ("issnet_serie_rps", "VARCHAR(10) NOT NULL DEFAULT ''"),
            ("issnet_ultimo_rps_conhecido", "integer NOT NULL DEFAULT 0"),
            ("issnet_numero_lote", "integer NOT NULL DEFAULT 0"),
        ]
        for col_name, col_def in columns_0046:
            cursor.execute(
                f"ALTER TABLE crm_vendas_config "
                f"ADD COLUMN IF NOT EXISTS {col_name} {col_def};",
            )
        # Migration 0047: certificado como BinaryField + nome (nunca apagar bytea existente)
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS issnet_certificado_nome VARCHAR(255) NOT NULL DEFAULT '';",
        )
        cursor.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'crm_vendas_config'
              AND column_name = 'issnet_certificado'
            """,
        )
        cert_col = cursor.fetchone()
        if cert_col is None:
            cursor.execute(
                "ALTER TABLE crm_vendas_config "
                "ADD COLUMN issnet_certificado bytea;",
            )
        elif cert_col[0] in ("character varying", "text"):
            # Legado FileField (caminho em varchar) → bytea; perde arquivo em disco antigo
            cursor.execute(
                "ALTER TABLE crm_vendas_config "
                "DROP COLUMN issnet_certificado;",
            )
            cursor.execute(
                "ALTER TABLE crm_vendas_config "
                "ADD COLUMN issnet_certificado bytea;",
            )
        # Se já é bytea: preservar dados do certificado
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS issnet_ambiente_homologacao boolean NOT NULL DEFAULT false;",
        )
        # Registrar migrations como aplicadas
        for mig_name in [
            "0045_add_asaas_loja_nf_fields",
            "0046_add_portal_emissor_fields",
            "0047_certificado_binary",
            "0049_crmconfig_issnet_ambiente_homologacao",
            "0059_crmconfig_asaas_webhook_token",
        ]:
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) "
                "SELECT %s, %s, %s "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM django_migrations WHERE app = %s AND name = %s"
                ");",
                ["crm_vendas", mig_name, timezone.now(), "crm_vendas", mig_name],
            )


def patch_crm_vendas_atividade_columns_if_missing(db_name: str) -> None:
    """Garante colunas das migrations 0056 (conta) e 0061 (lembretes WhatsApp) no tenant."""
    from django.db import connections
    from django.utils import timezone

    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError(f"Não foi possível configurar o banco {db_name}")

    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS conta_id BIGINT NULL;",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS crm_ativ_loja_conta_idx "
            "ON crm_vendas_atividade (loja_id, conta_id);",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS lembrete_whatsapp boolean NOT NULL DEFAULT false;",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS lembrete_whatsapp_telefone VARCHAR(20) NOT NULL DEFAULT '';",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS lembrete_24h_enviado_em TIMESTAMP WITH TIME ZONE NULL;",
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS lembrete_2h_enviado_em TIMESTAMP WITH TIME ZONE NULL;",
        )
        for mig_name in ("0056_atividade_conta", "0061_atividade_lembrete_whatsapp"):
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) "
                "SELECT %s, %s, %s "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM django_migrations WHERE app = %s AND name = %s"
                ");",
                ["crm_vendas", mig_name, timezone.now(), "crm_vendas", mig_name],
            )


def patch_atividade_lembrete_columns_if_missing(db_name: str) -> None:
    """Alias legado — preferir patch_crm_vendas_atividade_columns_if_missing."""
    patch_crm_vendas_atividade_columns_if_missing(db_name)
