"""
Script para executar migrations diretamente no schema da loja.
Solução para problema onde Django migrate ignora search_path.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


def executar_migrations_no_schema(database_name, schema_name, apps_to_migrate):
    """
    Executa migrations diretamente no schema usando SET LOCAL search_path.
    
    Args:
        database_name: Nome do banco configurado no Django
        schema_name: Nome do schema PostgreSQL
        apps_to_migrate: Lista de apps para migrar
    """
    conn = connections[database_name]
    conn.ensure_connection()
    
    # Usar transação para garantir que SET LOCAL funcione
    with conn.cursor() as cursor:
        # SET LOCAL só funciona dentro de transação
        cursor.execute('BEGIN')
        try:
            # Definir search_path para esta transação
            cursor.execute(f'SET LOCAL search_path TO "{schema_name}", public')
            logger.info(f"✅ SET LOCAL search_path executado: {schema_name},public")
            
            # Verificar
            cursor.execute('SHOW search_path')
            sp = cursor.fetchone()[0]
            logger.info(f"✅ search_path confirmado: {sp}")
            
            # Commit para aplicar SET LOCAL
            cursor.execute('COMMIT')
            
            # Agora executar migrations (na mesma conexão)
            for app in apps_to_migrate:
                logger.info(f"Executando migrate {app}...")
                call_command('migrate', app, '--database', database_name, verbosity=2)
                logger.info(f"✅ Migrations aplicadas: {app}")
                
        except Exception as e:
            cursor.execute('ROLLBACK')
            logger.error(f"❌ Erro ao executar migrations: {e}")
            raise


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python executar_migrations_schema.py <database_name> <schema_name> [app1 app2 ...]")
        sys.exit(1)
    
    database_name = sys.argv[1]
    schema_name = sys.argv[2]
    apps = sys.argv[3:] if len(sys.argv) > 3 else ['stores', 'products', 'crm_vendas']
    
    executar_migrations_no_schema(database_name, schema_name, apps)
