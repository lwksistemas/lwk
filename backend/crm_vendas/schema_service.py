"""
Serviço para configurar/recuperar schema do CRM.
Usado por: fix_loja_crm (command), auto-recovery nas views.
"""
import logging
import os

import dj_database_url
from django.conf import settings
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
        if db_name not in settings.DATABASES:
            default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
            settings.DATABASES[db_name] = {
                **default_db,
                'OPTIONS': {'options': f'-c search_path={schema_name},public'},
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'TIME_ZONE': None,
            }
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

        # 4. Marcar database_created na loja
        from superadmin.models import Loja
        if not loja.database_created:
            Loja.objects.filter(pk=loja.pk).update(database_created=True)
            logger.info(f"Loja {loja.slug} marcada como database_created=True")

        return True
    except Exception as e:
        logger.exception("configurar_schema_crm_loja: %s", e)
        return False
