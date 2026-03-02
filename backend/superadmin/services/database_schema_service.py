"""
Serviço para gerenciamento de schemas de banco de dados
Centraliza lógica de criação e configuração de schemas PostgreSQL
"""
import logging
import os
import re
from django.db import connection
from django.conf import settings
import dj_database_url

logger = logging.getLogger(__name__)


class DatabaseSchemaService:
    """
    Serviço responsável por criar e configurar schemas de banco de dados
    """
    
    @staticmethod
    def validar_nome_schema(schema_name: str) -> bool:
        """
        Valida nome do schema para evitar SQL injection
        
        Args:
            schema_name: Nome do schema a ser validado
            
        Returns:
            True se válido
            
        Raises:
            ValueError: Se nome for inválido
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
            raise ValueError(f"Nome de schema inválido: {schema_name}")
        return True
    
    @staticmethod
    def criar_schema(loja) -> bool:
        """
        Cria schema no PostgreSQL para a loja
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se criado com sucesso
            
        Raises:
            Exception: Se houver erro na criação
        """
        schema_name = loja.database_name.replace('-', '_')
        
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
        """
        Verifica se schema existe no banco
        
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
    def adicionar_configuracao_django(loja) -> bool:
        """
        Adiciona configuração do banco de dados no Django settings
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se adicionado com sucesso
        """
        schema_name = loja.database_name.replace('-', '_')
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        if not DATABASE_URL:
            logger.warning("DATABASE_URL não encontrada")
            return False
        
        try:
            # CONN_MAX_AGE=0 para não acumular conexões
            default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
            
            settings.DATABASES[loja.database_name] = {
                **default_db,
                'OPTIONS': {
                    'options': f'-c search_path={schema_name},public'
                },
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'TIME_ZONE': None,
            }
            
            logger.info(f"Configuração de banco adicionada para '{loja.database_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar configuração: {e}")
            return False
    
    @staticmethod
    def aplicar_migrations(loja) -> bool:
        """
        Aplica migrations no schema da loja
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se aplicado com sucesso
        """
        from django.core.management import call_command
        
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
        
        # Apps base
        base_apps = ['stores', 'products']
        
        # Apps por tipo de app
        tipo_apps = {
            'clinica-de-estetica': ['clinica_estetica'],
            'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
            'crm-vendas': ['crm_vendas'],
            'e-commerce': ['ecommerce'],
            'restaurante': ['restaurante'],
            'servicos': ['servicos'],
            'cabeleireiro': ['cabeleireiro'],
        }
        
        apps_to_migrate = base_apps + tipo_apps.get(tipo_slug, [])
        
        try:
            for app in apps_to_migrate:
                try:
                    call_command('migrate', app, '--database', loja.database_name, verbosity=0)
                    logger.info(f"Migrations aplicadas: {app}")
                except Exception as e:
                    logger.warning(f"Erro ao aplicar migration {app}: {e}")
            
            logger.info(f"Tabelas criadas no schema '{loja.database_name}' via migrations")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar migrations: {e}")
            return False
    
    @staticmethod
    def configurar_schema_completo(loja) -> bool:
        """
        Executa todo o processo de configuração do schema
        
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
            
            # 3. Adicionar configuração Django
            DatabaseSchemaService.adicionar_configuracao_django(loja)
            
            # 4. Aplicar migrations
            DatabaseSchemaService.aplicar_migrations(loja)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar schema completo: {e}")
            return False
