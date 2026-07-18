"""Serviço para gerenciamento de schemas de banco de dados.
Centraliza lógica de criação e configuração de schemas PostgreSQL.

Isolamento por loja:
- Ao criar uma loja (LojaCreateSerializer), é chamado configurar_schema_completo(loja).
- Isso cria um schema PostgreSQL exclusivo (ex: loja_clinica_vida_5889) e aplica as
  migrations nesse schema. Assim o backup e a aplicação usam apenas as tabelas desse
  schema, sem risco de misturar dados de outras lojas ou do superadmin.
"""
import contextlib
import logging
import re

from django.conf import settings
from django.db import connection, connections

logger = logging.getLogger(__name__)


def _pg_objects_already_exist(exc: BaseException) -> bool:
    """True quando o SQL da migration falhou só porque tabela/índice/sequence já existe no schema."""
    text = str(exc).lower()
    if "already exists" in text:
        return True
    if "duplicate" in text and any(
        k in text for k in ("relation", "table", "index", "constraint", "sequence")
    ):
        return True
    cause = getattr(exc, "__cause__", None)
    if cause is not None and cause is not exc:
        return _pg_objects_already_exist(cause)
    return False


def _record_migration_if_missing(alias: str, schema_name: str, app_label: str, migration_name: str) -> None:
    """Marca migration como aplicada (equivalente a migrate --fake) se ainda não estiver em django_migrations."""
    conn = connections[alias]
    with conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema_name}", public')
        cur.execute(
            """
            INSERT INTO django_migrations (app, name, applied)
            SELECT %s, %s, NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM django_migrations WHERE app = %s AND name = %s
            )
            """,
            [app_label, migration_name, app_label, migration_name],
        )


def _prefixos_tabela_app(app_label: str) -> list[str]:
    """Prefixos de table_name usados para detectar se o app já tem tabelas no schema."""
    if app_label == "clinica_estetica":
        return ["clinica_"]
    if app_label == "contenttypes":
        return ["django_content_type"]
    if app_label == "crm_vendas":
        # models/financeiro.py usa crm_financeiro_*; demais usam crm_vendas_*
        return ["crm_vendas_", "crm_financeiro_"]
    return [f"{app_label}_"]


def _contar_tabelas_app_no_schema(conn, schema_name: str, app_label: str) -> int:
    prefixes = _prefixos_tabela_app(app_label)
    or_parts = " OR ".join(["table_name LIKE %s"] * len(prefixes))
    params: list[str] = [schema_name] + [f"{p}%" for p in prefixes]
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
              AND ({or_parts})
            """,
            params,
        )
        return int(cur.fetchone()[0])


def _rollback_and_reconnect(alias: str) -> None:
    """Após erro em cur.execute(sql) com script multi-statement (ex.: BEGIN do sqlmigrate),
    só rollback pode não bastar; fecha e reabre a conexão do tenant.
    """
    if alias not in connections:
        return
    conn = connections[alias]
    with contextlib.suppress(Exception):
        conn.rollback()
    with contextlib.suppress(Exception):
        conn.close()
    with contextlib.suppress(Exception):
        conn.ensure_connection()


def _reset_tenant_connection(alias: str) -> None:
    """Evita 'current transaction is aborted' em requisições seguintes (ex.: re-auditoria)."""
    if alias not in connections:
        return
    conn = connections[alias]
    with contextlib.suppress(Exception):
        conn.rollback()
    with contextlib.suppress(Exception):
        conn.close()

# Apps extras por slug de TipoLoja (única fonte para migrate / auditoria)
TIPO_LOJA_EXTRA_APPS = {
    "clinica-de-estetica": ["clinica_beleza", "whatsapp", "crm_vendas", "nfse_integration"],
    "clinica-estetica": ["clinica_beleza", "whatsapp", "crm_vendas", "nfse_integration"],
    "clinica-da-beleza": ["clinica_beleza", "whatsapp", "crm_vendas", "nfse_integration"],
    "clinica-beleza": ["clinica_beleza", "whatsapp", "crm_vendas", "nfse_integration"],
    "e-commerce": ["ecommerce"],
    "ecommerce": ["ecommerce"],
    "restaurante": ["restaurante"],
    "servicos": ["servicos"],
    "cabeleireiro": ["cabeleireiro", "whatsapp", "nfse_integration"],
    "crm-vendas": ["crm_vendas", "nfse_integration", "whatsapp"],
    "hotel-pousada": ["hotel"],
    "hotel": ["hotel"],
}

# Falha de migration nestes apps aborta criação/recuperação de loja tipo CRM Vendas (NFS-e no tenant).
APPS_CRITICOS_MIGRACAO_CRM_VENDAS = frozenset({"crm_vendas", "nfse_integration"})


def get_apps_esperados_para_loja(loja) -> list[str]:
    """Apps cujo schema deve existir para esta loja (alinhado a aplicar_migrations).
    contenttypes e auth são migrados para evitar erros do Django, mas não precisam
    ser auditados (não criam tabelas com prefixo próprio em todos os schemas).
    """
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() or "unknown"
    base = ["contenttypes", "auth", "stores", "products"]
    return base + TIPO_LOJA_EXTRA_APPS.get(tipo_slug, [])


class DatabaseSchemaService:
    """Serviço responsável por criar e configurar schemas de banco de dados
    """

    @staticmethod
    def validar_nome_schema(schema_name: str) -> bool:
        """Valida nome do schema para evitar SQL injection

        Args:
            schema_name: Nome do schema a ser validado

        Returns:
            True se válido

        Raises:
            ValueError: Se nome for inválido

        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            raise ValueError(f"Nome de schema inválido: {schema_name}")
        return True

    @staticmethod
    def criar_schema(loja) -> bool:
        """Cria schema no PostgreSQL para a loja

        Args:
            loja: Objeto Loja

        Returns:
            True se criado com sucesso

        Raises:
            Exception: Se houver erro na criação

        """
        schema_name = loja.database_name.replace("-", "_")

        try:
            # Validar nome
            DatabaseSchemaService.validar_nome_schema(schema_name)

            # Criar schema
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')

            logger.info(f"Schema '{schema_name}' criado no PostgreSQL")

            # Verificar criação
            if not DatabaseSchemaService.verificar_schema_existe(schema_name):
                raise Exception(f"Schema '{schema_name}' não foi criado corretamente!")

            logger.info(f"Schema '{schema_name}' verificado e confirmado")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar schema '{schema_name}': {e}")
            raise

    @staticmethod
    def verificar_schema_existe(schema_name: str) -> bool:
        """Verifica se schema existe no banco

        Args:
            schema_name: Nome do schema

        Returns:
            True se existe

        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.schemata
                WHERE schema_name = %s
            """, [schema_name])
            return cursor.fetchone()[0] > 0



    @staticmethod
    def _get_migrations_to_apply(conn, app, schema_name):
        """Retorna lista ordenada de (app_label, migration_name) pendentes para o app."""
        from django.db.migrations.executor import MigrationExecutor
        from django.db.migrations.loader import MigrationLoader
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema_name}", public')
            cur.execute("SELECT name FROM django_migrations WHERE app = %s", [app])
            applied = {row[0] for row in cur.fetchall()}
        loader = MigrationLoader(conn)
        migrations_to_apply = []
        if app in loader.migrated_apps:
            executor = MigrationExecutor(conn)
            app_migrations = [k for k in loader.graph.nodes if k[0] == app and k[1] not in applied]
            if app_migrations:
                plan = []
                for migration_key in app_migrations:
                    try:
                        for mig in executor.loader.graph.forwards_plan(migration_key):
                            if mig[0] == app and mig[1] not in applied and mig not in plan:
                                plan.append(mig)
                    except Exception as e:
                        logger.warning("      ⚠️  Erro ao obter plan para %s: %s", migration_key, e)
                migrations_to_apply = plan
        if not migrations_to_apply:
            migrations_to_apply = sorted(
                [k for k in loader.graph.nodes if k[0] == app and k[1] not in applied],
                key=lambda x: x[1],
            )
        return migrations_to_apply, applied

    @staticmethod
    def _apply_single_migration(conn, loja_database_name, schema_name, app_label, migration_name, tipo_slug, app):
        """Executa SQL de uma migration no schema; faz fake se objetos já existem."""
        from io import StringIO

        from django.core.management import call_command
        try:
            sql_out = StringIO()
            call_command("sqlmigrate", app_label, migration_name, "--database", loja_database_name, stdout=sql_out)
            sql = sql_out.getvalue()
            if not sql or sql.strip() == "--":
                logger.info("      ⚠️  Migration %s sem SQL", migration_name)
                _record_migration_if_missing(loja_database_name, schema_name, app_label, migration_name)
                return
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema_name}", public')
                cur.execute(sql)
                cur.execute("INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())", [app_label, migration_name])
            logger.info("      ✅ %s", migration_name)
        except Exception as e:
            logger.error("      ❌ Erro em %s: %s", migration_name, e)
            _rollback_and_reconnect(loja_database_name)
            if _pg_objects_already_exist(e):
                logger.warning("      ⚠️  Objetos já existem no schema; registrando %s como aplicada (--fake).", migration_name)
                try:
                    _record_migration_if_missing(loja_database_name, schema_name, app_label, migration_name)
                except Exception as fake_err:
                    logger.error("      ❌ Falha ao registrar migration fake: %s", fake_err)
            if tipo_slug == "crm-vendas" and app in APPS_CRITICOS_MIGRACAO_CRM_VENDAS and not _pg_objects_already_exist(e):
                raise

    @staticmethod
    def _verify_schema_tables(conn, schema_name, apps_to_migrate):
        """Verifica que o schema tem tabelas após migrations. Levanta RuntimeError se vazio."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'django_%%'",
                [schema_name],
            )
            tabelas_count = cur.fetchone()[0]
        if tabelas_count == 0:
            logger.error("❌ ERRO CRÍTICO: Schema '%s' está VAZIO após migrations! Apps tentados: %s.", schema_name, apps_to_migrate)
            raise RuntimeError(
                f"Schema '{schema_name}' está vazio após migrations. "
                "As tabelas não foram criadas no schema correto. "
                "Entre em contato com o suporte técnico.",
            )
        logger.info("✅ Schema '%s' criado com sucesso: %s tabela(s)", schema_name, tabelas_count)

    @staticmethod
    def aplicar_migrations(loja) -> bool:
        """Aplica migrations no schema da loja executando SQL diretamente.

        CORREÇÃO v1016: Django call_command('migrate') ignora search_path COMPLETAMENTE.
        Solução DEFINITIVA: Obter SQL das migrations e executar diretamente no schema.
        """
        from core.db_config import ensure_loja_database_config

        if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
            raise RuntimeError(
                f"Não foi possível adicionar configuração do banco '{loja.database_name}'. "
                "Verifique se DATABASE_URL está definida.",
            )
        if loja.database_name not in settings.DATABASES:
            raise RuntimeError(f"Config do banco '{loja.database_name}' não encontrada em settings.DATABASES!")

        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() or "unknown"
        apps_to_migrate = get_apps_esperados_para_loja(loja)
        schema_name = loja.database_name.replace("-", "_")

        try:
            conn = connections[loja.database_name]
            conn.ensure_connection()
            logger.info("🚀 Iniciando migrations manuais para schema '%s'", schema_name)

            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema_name}", public')
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS django_migrations (
                        id SERIAL PRIMARY KEY,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                logger.info("✅ Tabela django_migrations criada em '%s'", schema_name)
                # WhatsApp 0002 depende de superadmin.0001 no histórico; tabelas ficam no public.
                cur.execute(
                    """
                    SELECT EXISTS (
                      SELECT 1 FROM django_migrations
                      WHERE app = 'whatsapp' AND name LIKE '0002%%'
                    )
                    """,
                )
                if cur.fetchone()[0]:
                    _record_migration_if_missing(
                        loja.database_name, schema_name, "superadmin", "0001_initial",
                    )

            for app in apps_to_migrate:
                try:
                    logger.info("📦 Processando app: %s", app)
                    migrations_to_apply, applied = DatabaseSchemaService._get_migrations_to_apply(conn, app, schema_name)
                    if not migrations_to_apply:
                        logger.info("   ℹ️  Nenhuma migration pendente para %s", app)
                        continue
                    n_tab_app = _contar_tabelas_app_no_schema(conn, schema_name, app)
                    if n_tab_app > 0 and len(applied) == 0:
                        logger.warning(
                            "   ⚠️  App %s: %s tabela(s) sem histórico. Registrando %s migration(s) como fake.",
                            app, n_tab_app, len(migrations_to_apply),
                        )
                        for app_label, migration_name in migrations_to_apply:
                            _record_migration_if_missing(loja.database_name, schema_name, app_label, migration_name)
                        continue
                    logger.info("   📝 %s migration(s) pendente(s)", len(migrations_to_apply))
                    for app_label, migration_name in migrations_to_apply:
                        DatabaseSchemaService._apply_single_migration(conn, loja.database_name, schema_name, app_label, migration_name, tipo_slug, app)
                        conn = connections[loja.database_name]
                    logger.info("   ✅ App %s concluído", app)
                except Exception as e:
                    logger.error("❌ Erro ao processar app %s: %s", app, e)
                    _rollback_and_reconnect(loja.database_name)
                    conn = connections[loja.database_name]
                    if tipo_slug == "crm-vendas" and app in APPS_CRITICOS_MIGRACAO_CRM_VENDAS:
                        raise
                    logger.warning("Continuando apesar do erro em %s", app)

            _rollback_and_reconnect(loja.database_name)
            conn = connections[loja.database_name]
            DatabaseSchemaService._verify_schema_tables(conn, schema_name, apps_to_migrate)
            logger.info("🎉 Migrations concluídas para '%s'", loja.database_name)
            return True
        except Exception as e:
            logger.error("Erro ao aplicar migrations: %s", e)
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            _reset_tenant_connection(loja.database_name)

    @staticmethod
    def _mover_tabelas_public_para_schema(loja, schema_name: str, apps_to_migrate: list) -> None:
        """Fallback: se migrate criou tabelas em public, move-as para o schema da loja.

        CORREÇÃO v983: Melhorado para ser mais robusto e informativo.
        """
        from django.db import connections
        try:
            DatabaseSchemaService.validar_nome_schema(schema_name)
        except ValueError:
            logger.warning(f"Nome de schema inválido: {schema_name}")
            return

        app_prefixes = [f"{app}_" for app in apps_to_migrate]

        try:
            conn = connections[loja.database_name]
            conn.ensure_connection()
            with conn.cursor() as cur:
                # Verificar se schema já tem tabelas (não precisa mover)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                    AND table_name NOT LIKE 'django_%%'
                    """,
                    [schema_name],
                )
                if cur.fetchone()[0] > 0:
                    logger.info(f"Schema '{schema_name}' já possui tabelas, não precisa mover")
                    return

                # Buscar tabelas em public que pertencem aos apps da loja
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """,
                )
                todas = [r[0] for r in cur.fetchall()]
                tabelas_mover = [t for t in todas if any(t.startswith(p) for p in app_prefixes)]

                if not tabelas_mover:
                    logger.warning(
                        f"⚠️  Nenhuma tabela encontrada em 'public' para mover para '{schema_name}'. "
                        f"Apps esperados: {apps_to_migrate}",
                    )
                    return

                logger.info(
                    f"🔄 Fallback ativado: movendo {len(tabelas_mover)} tabela(s) "
                    f"de 'public' para '{schema_name}'",
                )

                # Mover django_migrations primeiro (se existir)
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'django_migrations'
                    )
                    """,
                )

                if cur.fetchone()[0]:
                    # Buscar migrations dos apps da loja
                    cur.execute(
                        "SELECT app, name, applied FROM public.django_migrations WHERE app = ANY(%s)",
                        [apps_to_migrate],
                    )
                    migracoes = cur.fetchall()

                    if migracoes:
                        # Criar tabela django_migrations no schema
                        cur.execute(
                            f"""
                            CREATE TABLE IF NOT EXISTS "{schema_name}".django_migrations (
                                id SERIAL PRIMARY KEY,
                                app VARCHAR(255) NOT NULL,
                                name VARCHAR(255) NOT NULL,
                                applied TIMESTAMPTZ NOT NULL
                            )
                            """,
                        )

                        # Copiar migrations
                        for app, name, applied in migracoes:
                            cur.execute(
                                f'INSERT INTO "{schema_name}".django_migrations (app, name, applied) VALUES (%s, %s, %s)',
                                [app, name, applied],
                            )

                        # Remover de public
                        cur.execute(
                            "DELETE FROM public.django_migrations WHERE app = ANY(%s)",
                            [apps_to_migrate],
                        )

                        logger.info(f"✅ {len(migracoes)} migration(s) movida(s) para '{schema_name}'")

                # Mover tabelas
                tabelas_movidas = 0
                for table_name in tabelas_mover:
                    if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
                        try:
                            cur.execute(f'ALTER TABLE public."{table_name}" SET SCHEMA "{schema_name}"')
                            tabelas_movidas += 1
                            logger.info(f"✅ Tabela {table_name} movida para {schema_name}")
                        except Exception as e:
                            logger.error(f"❌ Erro ao mover {table_name}: {e}")
                    else:
                        logger.warning(f"⚠️  Nome de tabela inválido (ignorado): {table_name}")

                logger.info(
                    f"✅ Fallback concluído: {tabelas_movidas}/{len(tabelas_mover)} tabela(s) "
                    f"movida(s) para '{schema_name}'",
                )

        except Exception as e:
            logger.error(f"❌ Erro no fallback de movimentação de tabelas: {e}")
            import traceback
            logger.error(traceback.format_exc())

    @staticmethod
    def configurar_schema_completo(loja) -> bool:
        """Executa todo o processo de configuração do schema individual da loja.
        Deve ser chamado na criação da loja para garantir banco/schema isolado
        e evitar que o backup exporte dados de outras lojas ou do superadmin.

        Passos: criar schema -> marcar database_created -> aplicar migrations.

        Args:
            loja: Objeto Loja

        Returns:
            True se configurado com sucesso

        """
        try:
            # 1. Criar schema
            DatabaseSchemaService.criar_schema(loja)

            # 2. Marcar como criado
            loja.database_created = True
            loja.save()

            # 3. Aplicar migrations (já adiciona configuração Django internamente)
            if not DatabaseSchemaService.aplicar_migrations(loja):
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() or "unknown"
                raise RuntimeError(
                    f"Falha ao aplicar migrations no schema da loja (tipo: {tipo_slug}). "
                    "O cadastro não pode ser concluído sem as tabelas do app.",
                )

            # Catálogo padrão (locais + procedimentos) para novas lojas Clínica da Beleza
            try:
                from clinica_beleza.catalogo_service import aplicar_catalogo_padrao, is_clinica_beleza_loja
                if is_clinica_beleza_loja(loja):
                    aplicar_catalogo_padrao(loja)
            except Exception as catalogo_exc:
                logger.warning(
                    "Catálogo padrão Clínica da Beleza não aplicado em %s: %s",
                    loja.slug,
                    catalogo_exc,
                )

            return True
        except Exception:
            logger.exception("configurar_schema_completo")
            raise
