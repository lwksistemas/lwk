"""
Serviço para configurar/recuperar schema do CRM.
Usado por: fix_loja_crm (command), auto-recovery nas views.

Deve aplicar os mesmos apps que DatabaseSchemaService na criação da loja
(inclui nfse_integration para lojas CRM — NFS-e no schema isolado).
"""
import logging
import os

from django.db import connection, connections
from django.core.management import call_command

from superadmin.services.database_schema_service import (
    APPS_CRITICOS_MIGRACAO_CRM_VENDAS,
    get_apps_esperados_para_loja,
)

logger = logging.getLogger(__name__)


def configurar_schema_crm_loja(loja) -> bool:
    """
    Configura schema e tabelas CRM para uma loja.
    Cria schema se não existir, aplica migrations, adiciona colunas faltantes.

    Returns:
        True se configurado com sucesso, False caso contrário.
    """
    if not loja:
        return False

    db_name = loja.database_name
    schema_name = db_name.replace('-', '_')
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'crm-vendas'

    DATABASE_URL = os.environ.get('DATABASE_URL')
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
                [schema_name]
            )
            if not cursor.fetchone():
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                logger.info(f"Schema '{schema_name}' criado")

        # 3. Aplicar migrations (mesma lista que criar loja: get_apps_esperados_para_loja)
        apps = get_apps_esperados_para_loja(loja)

        for app in apps:
            try:
                conn = connections[db_name]
                conn.ensure_connection()
                with conn.cursor() as cur:
                    cur.execute(f'SET search_path TO "{schema_name}", public')
                call_command('migrate', app, '--database', db_name, verbosity=0)
                logger.info(f"Migrations aplicadas: {app}")
            except Exception as e:
                if tipo_slug == 'crm-vendas' and app in APPS_CRITICOS_MIGRACAO_CRM_VENDAS:
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

        # 5. Fechar conexão para forçar nova conexão com schema correto no retry
        if db_name in connections:
            try:
                connections[db_name].close()
            except Exception:
                pass

        return True
    except Exception as e:
        logger.exception("configurar_schema_crm_loja: %s", e)
        return False


def patch_crm_vendas_asaas_columns_if_missing(db_name: str) -> None:
    """
    Garante colunas da migration 0045 (asaas_api_key, asaas_sandbox) no schema do tenant.
    Movido de views.py (refatoração #10 — SRP: DDL não pertence a views).
    """
    from django.db import connections
    from django.utils import timezone
    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db_name, conn_max_age=0):
        raise RuntimeError(f'Não foi possível configurar o banco {db_name}')

    conn = connections[db_name]
    with conn.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS asaas_api_key VARCHAR(255) NOT NULL DEFAULT '';"
        )
        cursor.execute(
            "ALTER TABLE crm_vendas_config "
            "ADD COLUMN IF NOT EXISTS asaas_sandbox boolean NOT NULL DEFAULT false;"
        )
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) "
            "SELECT %s, %s, %s "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM django_migrations WHERE app = %s AND name = %s"
            ");",
            ['crm_vendas', '0045_add_asaas_loja_nf_fields', timezone.now(),
             'crm_vendas', '0045_add_asaas_loja_nf_fields'],
        )
