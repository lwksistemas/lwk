"""
Backend PostgreSQL que define search_path ao conectar.
Usado para bancos de loja (loja_*) onde as tabelas ficam em schemas isolados.

Necessário porque OPTIONS['options'] com search_path pode ser ignorado por
PgBouncer ou em ambientes com connection pooling (ex: Heroku).
"""
import logging
import re
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

    def get_new_connection(self, conn_params):
        """
        Cria nova conexão e define search_path IMEDIATAMENTE.
        Isso garante que TODAS as operações (incluindo migrations) usem o schema correto.
        
        CORREÇÃO v1002: Adicionar search_path aos parâmetros de conexão ANTES de conectar.
        Isso evita problemas com transações e garante que o schema seja definido desde o início.
        """
        # Definir search_path nos parâmetros de conexão ANTES de criar a conexão
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name and isinstance(schema_name, str):
            # Validar para evitar SQL injection (apenas alfanumérico e underscore)
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
                # Adicionar options ao conn_params para definir search_path
                if 'options' not in conn_params:
                    conn_params['options'] = ''
                
                # Adicionar search_path às options (formato PostgreSQL)
                search_path_option = f'-c search_path="{schema_name}",public'
                if conn_params['options']:
                    conn_params['options'] += f' {search_path_option}'
                else:
                    conn_params['options'] = search_path_option
                
                logger.info(f"✅ search_path '{schema_name}' adicionado aos parâmetros de conexão")
            else:
                logger.warning(f"⚠️  Nome de schema inválido (ignorado): {schema_name}")
        
        # Criar conexão com search_path já definido
        connection = super().get_new_connection(conn_params)
        
        return connection

    def init_connection_state(self):
        """
        Inicializa estado da conexão.
        O search_path já foi definido em get_new_connection(), mas verificamos aqui.
        """
        super().init_connection_state()
        
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name and isinstance(schema_name, str):
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
                try:
                    with self.connection.cursor() as cursor:
                        # Verificar se search_path está correto
                        cursor.execute('SHOW search_path')
                        current_path = cursor.fetchone()[0]
                        
                        if schema_name not in current_path:
                            # Redefinir se necessário (dentro de transação é OK aqui)
                            cursor.execute(f'SET search_path TO "{schema_name}", public')
                            logger.warning(f"⚠️  search_path redefinido para '{schema_name}' (estava: {current_path})")
                        else:
                            logger.info(f"✅ search_path confirmado: {current_path}")
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar/definir search_path: {e}")
