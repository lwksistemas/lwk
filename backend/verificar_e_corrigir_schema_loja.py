#!/usr/bin/env python
"""
Script para verificar e corrigir schema de uma loja antes de importar backup

Uso:
    python verificar_e_corrigir_schema_loja.py <loja_id>
    
Exemplo:
    python verificar_e_corrigir_schema_loja.py 35
"""

import os
import sys
import django

# Setup Django
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.db import connections
from django.core.management import call_command
from superadmin.models import Loja
from superadmin.services.database_schema_service import DatabaseSchemaService
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def verificar_tabelas_schema(loja):
    """Verifica quais tabelas existem no schema da loja"""
    database_name = loja.database_name
    schema_name = database_name.replace('-', '_')
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Verificando schema da loja: {loja.nome}")
    logger.info(f"Database name: {database_name}")
    logger.info(f"Schema PostgreSQL: {schema_name}")
    logger.info(f"{'='*60}\n")
    
    # Verificar se a configuração do banco existe
    if database_name not in connections.databases:
        logger.warning(f"⚠️ Banco '{database_name}' não está em settings.DATABASES")
        logger.info("Adicionando configuração do banco...")
        if DatabaseSchemaService.adicionar_configuracao_django(loja):
            logger.info("✅ Configuração adicionada com sucesso")
        else:
            logger.error("❌ Falha ao adicionar configuração")
            return False
    
    # Conectar ao banco
    try:
        connection = connections[database_name]
        with connection.cursor() as cursor:
            # Verificar se o schema existe
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name]
            )
            schema_exists = cursor.fetchone() is not None
            
            if not schema_exists:
                logger.warning(f"⚠️ Schema '{schema_name}' não existe")
                logger.info("Criando schema...")
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                logger.info("✅ Schema criado")
            else:
                logger.info(f"✅ Schema '{schema_name}' existe")
            
            # Listar tabelas no schema
            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                ORDER BY table_name
                """,
                [schema_name]
            )
            tabelas = [row[0] for row in cursor.fetchall()]
            
            if tabelas:
                logger.info(f"\n✅ Encontradas {len(tabelas)} tabelas no schema:")
                for tabela in tabelas:
                    logger.info(f"   - {tabela}")
            else:
                logger.warning(f"\n⚠️ Nenhuma tabela encontrada no schema '{schema_name}'")
                return False
            
            # Verificar tabelas específicas do CRM Vendas
            tabelas_crm = [
                'crm_vendas_vendedor',
                'crm_vendas_conta',
                'crm_vendas_lead',
                'crm_vendas_oportunidade',
                'crm_vendas_atividade',
                'crm_vendas_contato',
                'crm_vendas_config',
            ]
            
            logger.info(f"\nVerificando tabelas do CRM Vendas:")
            faltando = []
            for tabela in tabelas_crm:
                existe = tabela in tabelas
                status = "✅" if existe else "❌"
                logger.info(f"   {status} {tabela}")
                if not existe:
                    faltando.append(tabela)
            
            if faltando:
                logger.warning(f"\n⚠️ Faltam {len(faltando)} tabelas do CRM Vendas")
                return False
            else:
                logger.info(f"\n✅ Todas as tabelas do CRM Vendas existem!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar schema: {e}")
        import traceback
        traceback.print_exc()
        return False


def aplicar_migrations(loja):
    """Aplica migrations no schema da loja"""
    logger.info(f"\n{'='*60}")
    logger.info("Aplicando migrations...")
    logger.info(f"{'='*60}\n")
    
    try:
        if DatabaseSchemaService.aplicar_migrations(loja):
            logger.info("✅ Migrations aplicadas com sucesso")
            return True
        else:
            logger.error("❌ Falha ao aplicar migrations")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao aplicar migrations: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python verificar_e_corrigir_schema_loja.py <loja_id>")
        print("Exemplo: python verificar_e_corrigir_schema_loja.py 35")
        sys.exit(1)
    
    loja_id = int(sys.argv[1])
    
    try:
        loja = Loja.objects.get(id=loja_id)
    except Loja.DoesNotExist:
        logger.error(f"❌ Loja com ID {loja_id} não encontrada")
        sys.exit(1)
    
    logger.info(f"\n{'#'*60}")
    logger.info(f"# VERIFICAÇÃO E CORREÇÃO DE SCHEMA")
    logger.info(f"# Loja: {loja.nome} (ID: {loja.id})")
    logger.info(f"# Slug: {loja.slug}")
    logger.info(f"# Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")
    logger.info(f"{'#'*60}\n")
    
    # Passo 1: Verificar estado atual
    tabelas_ok = verificar_tabelas_schema(loja)
    
    if tabelas_ok:
        logger.info(f"\n{'='*60}")
        logger.info("✅ SCHEMA OK - Pronto para importar backup!")
        logger.info(f"{'='*60}\n")
        sys.exit(0)
    
    # Passo 2: Aplicar migrations
    logger.info("\n⚠️ Schema incompleto. Aplicando migrations...\n")
    migrations_ok = aplicar_migrations(loja)
    
    if not migrations_ok:
        logger.error(f"\n{'='*60}")
        logger.error("❌ FALHA ao aplicar migrations")
        logger.error(f"{'='*60}\n")
        sys.exit(1)
    
    # Passo 3: Verificar novamente
    logger.info("\nVerificando schema após migrations...\n")
    tabelas_ok = verificar_tabelas_schema(loja)
    
    if tabelas_ok:
        logger.info(f"\n{'='*60}")
        logger.info("✅ SCHEMA CORRIGIDO - Pronto para importar backup!")
        logger.info(f"{'='*60}\n")
        sys.exit(0)
    else:
        logger.error(f"\n{'='*60}")
        logger.error("❌ SCHEMA AINDA INCOMPLETO após migrations")
        logger.error("Verifique os logs acima para mais detalhes")
        logger.error(f"{'='*60}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
