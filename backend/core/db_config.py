"""
Configuração centralizada de banco de dados para lojas (multi-tenant).

Único ponto que define ENGINE, SCHEMA_NAME e parâmetros de conexão.
Usado por: DatabaseSchemaService, TenantMiddleware, signals, backup, commands.
"""
import logging
import os
import re

import dj_database_url
from django.conf import settings

logger = logging.getLogger(__name__)


def get_loja_database_config(
    database_name: str,
    conn_max_age: int = 0,
) -> dict | None:
    """
    Retorna a configuração Django para banco de uma loja.

    Usa backend customizado (core.db_backends.postgresql_schema) que define
    search_path em init_connection_state - funciona com PgBouncer/Heroku.

    Args:
        database_name: Nome do banco (ex: loja_22239255889)
        conn_max_age: Tempo em segundos para manter conexão (0=fechar ao fim, 60=manter para migrations)

    Returns:
        dict de configuração ou None se DATABASE_URL não estiver definida
    """
    if not database_name:
        return None

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.warning("get_loja_database_config: DATABASE_URL não configurada")
        return None

    if 'postgres' not in database_url.lower():
        return None

    schema_name = database_name.replace('-', '_')
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
        logger.warning(f"get_loja_database_config: nome de schema inválido: {schema_name}")
        return None

    try:
        default_db = dj_database_url.config(default=database_url, conn_max_age=0)
        opts = dict(default_db.get('OPTIONS', {}) or {})
        base_opt = opts.get('options', '') or ''
        if '-c statement_timeout=' not in base_opt:
            opts['options'] = (base_opt + ' -c statement_timeout=25000').strip()

        return {
            **default_db,
            'ENGINE': 'core.db_backends.postgresql_schema',
            'OPTIONS': opts,
            'SCHEMA_NAME': schema_name,
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            'CONN_MAX_AGE': conn_max_age,
            'CONN_HEALTH_CHECKS': False,
            'TIME_ZONE': None,
        }
    except Exception as e:
        logger.warning(f"get_loja_database_config: erro ao gerar config: {e}")
        return None


def ensure_loja_database_config(database_name: str, conn_max_age: int = 0) -> bool:
    """
    Garante que o banco da loja está em settings.DATABASES.
    Adiciona a config se ainda não existir.

    Returns:
        True se configurado com sucesso
    """
    if not database_name or database_name in settings.DATABASES:
        return bool(database_name and database_name in settings.DATABASES)

    config = get_loja_database_config(database_name, conn_max_age)
    if not config:
        return False

    settings.DATABASES[database_name] = config
    logger.debug(f"Banco '{database_name}' configurado em settings.DATABASES")
    return True
