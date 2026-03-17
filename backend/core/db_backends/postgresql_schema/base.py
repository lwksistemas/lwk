"""
Backend PostgreSQL que define search_path ao conectar.
Usado para bancos de loja (loja_*) onde as tabelas ficam em schemas isolados.

Necessário porque OPTIONS['options'] com search_path pode ser ignorado por
PgBouncer ou em ambientes com connection pooling (ex: Heroku).
"""
import logging
from django.db.backends.postgresql.base import (
    DatabaseWrapper as BasePostgresWrapper,
    Database,
)

logger = logging.getLogger(__name__)


class DatabaseWrapper(BasePostgresWrapper):
    """
    Extende o backend PostgreSQL para definir search_path na conexão.
    O schema deve estar em settings_dict['SCHEMA_NAME'].
    """

    def init_connection_state(self):
        super().init_connection_state()
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name and isinstance(schema_name, str):
            # Validar para evitar SQL injection (apenas alfanumérico e underscore)
            import re
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{schema_name}", public')
                    logger.debug(f"search_path definido para schema '{schema_name}'")
                except Exception as e:
                    logger.warning(f"Erro ao definir search_path para '{schema_name}': {e}")
