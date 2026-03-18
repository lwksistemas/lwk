# Script para criar colunas de assinatura em propostas e contratos
# Executar no Django shell do Heroku: heroku run python backend/manage.py shell

from django.db import connection

def criar_colunas_assinatura():
    """Cria as colunas nome_vendedor_assinatura e nome_cliente_assinatura nas tabelas de propostas e contratos."""
    
    with connection.cursor() as cursor:
        # Verificar se as colunas já existem em Proposta
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='crm_vendas_proposta' 
            AND column_name IN ('nome_vendedor_assinatura', 'nome_cliente_assinatura');
        """)
        colunas_proposta = [row[0] for row in cursor.fetchall()]
        
        # Criar colunas em Proposta se não existirem
        if 'nome_vendedor_assinatura' not in colunas_proposta:
            print("Criando coluna nome_vendedor_assinatura em crm_vendas_proposta...")
            cursor.execute("""
                ALTER TABLE crm_vendas_proposta 
                ADD COLUMN nome_vendedor_assinatura VARCHAR(255) NULL;
            """)
            print("✅ Coluna nome_vendedor_assinatura criada em crm_vendas_proposta")
        else:
            print("ℹ️  Coluna nome_vendedor_assinatura já existe em crm_vendas_proposta")
        
        if 'nome_cliente_assinatura' not in colunas_proposta:
            print("Criando coluna nome_cliente_assinatura em crm_vendas_proposta...")
            cursor.execute("""
                ALTER TABLE crm_vendas_proposta 
                ADD COLUMN nome_cliente_assinatura VARCHAR(255) NULL;
            """)
            print("✅ Coluna nome_cliente_assinatura criada em crm_vendas_proposta")
        else:
            print("ℹ️  Coluna nome_cliente_assinatura já existe em crm_vendas_proposta")
        
        # Verificar se as colunas já existem em Contrato
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='crm_vendas_contrato' 
            AND column_name IN ('nome_vendedor_assinatura', 'nome_cliente_assinatura');
        """)
        colunas_contrato = [row[0] for row in cursor.fetchall()]
        
        # Criar colunas em Contrato se não existirem
        if 'nome_vendedor_assinatura' not in colunas_contrato:
            print("Criando coluna nome_vendedor_assinatura em crm_vendas_contrato...")
            cursor.execute("""
                ALTER TABLE crm_vendas_contrato 
                ADD COLUMN nome_vendedor_assinatura VARCHAR(255) NULL;
            """)
            print("✅ Coluna nome_vendedor_assinatura criada em crm_vendas_contrato")
        else:
            print("ℹ️  Coluna nome_vendedor_assinatura já existe em crm_vendas_contrato")
        
        if 'nome_cliente_assinatura' not in colunas_contrato:
            print("Criando coluna nome_cliente_assinatura em crm_vendas_contrato...")
            cursor.execute("""
                ALTER TABLE crm_vendas_contrato 
                ADD COLUMN nome_cliente_assinatura VARCHAR(255) NULL;
            """)
            print("✅ Coluna nome_cliente_assinatura criada em crm_vendas_contrato")
        else:
            print("ℹ️  Coluna nome_cliente_assinatura já existe em crm_vendas_contrato")
    
    print("\n✅ Processo concluído!")
    print("\nVerificando estrutura das tabelas:")
    
    with connection.cursor() as cursor:
        # Verificar colunas de Proposta
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='crm_vendas_proposta' 
            AND column_name LIKE '%assinatura%'
            ORDER BY column_name;
        """)
        print("\n📋 Colunas de assinatura em crm_vendas_proposta:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Verificar colunas de Contrato
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='crm_vendas_contrato' 
            AND column_name LIKE '%assinatura%'
            ORDER BY column_name;
        """)
        print("\n📋 Colunas de assinatura em crm_vendas_contrato:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")

# Executar
criar_colunas_assinatura()
