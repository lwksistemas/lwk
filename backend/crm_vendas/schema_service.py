"""
Serviço para configurar/recuperar schema do CRM.
Usado por: fix_loja_crm (command), auto-recovery nas views.
"""
import logging
import os

from django.db import connection, connections
from django.core.management import call_command

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

        # 3. Aplicar migrations
        base_apps = ['stores', 'products']
        tipo_apps = {
            'crm-vendas': ['crm_vendas'],
            'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
            'clinica-de-estetica': ['clinica_estetica'],
            'e-commerce': ['ecommerce'],
            'restaurante': ['restaurante'],
            'servicos': ['servicos'],
            'cabeleireiro': ['cabeleireiro'],
        }
        apps = base_apps + tipo_apps.get(tipo_slug, ['crm_vendas'])

        for app in apps:
            try:
                conn = connections[db_name]
                conn.ensure_connection()
                with conn.cursor() as cur:
                    cur.execute(f'SET search_path TO "{schema_name}", public')
                call_command('migrate', app, '--database', db_name, verbosity=0)
                logger.info(f"Migrations aplicadas: {app}")
            except Exception as e:
                if tipo_slug == 'crm-vendas' and app == 'crm_vendas':
                    logger.error(f"Erro crítico ao aplicar migration crm_vendas: {e}")
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
