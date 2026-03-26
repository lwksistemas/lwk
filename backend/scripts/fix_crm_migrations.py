#!/usr/bin/env python
"""
Script para corrigir migrations do CRM nas lojas que não têm as tabelas criadas.
Aplica as migrations diretamente usando SQL.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja


def check_crm_tables_exist(schema_name):
    """Verifica se as tabelas do CRM existem no schema."""
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s
                AND table_name = 'crm_vendas_vendedor'
            )
        """, [schema_name])
        return cursor.fetchone()[0]


def create_crm_tables(schema_name):
    """Cria as tabelas do CRM no schema usando SQL direto."""
    print(f"  📝 Criando tabelas do CRM no schema {schema_name}...")
    
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}")
        
        # SQL para criar as tabelas do CRM
        sql = """
        -- Tabela de Vendedores
        CREATE TABLE IF NOT EXISTS crm_vendas_vendedor (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(200) NOT NULL,
            email VARCHAR(254),
            telefone VARCHAR(20),
            cargo VARCHAR(100) DEFAULT 'Vendedor',
            comissao_padrao DECIMAL(5, 2) DEFAULT 0,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_vend_loja_active_idx ON crm_vendas_vendedor(loja_id, is_active);
        CREATE INDEX IF NOT EXISTS crm_vend_loja_email_idx ON crm_vendas_vendedor(loja_id, email);
        
        -- Tabela de Contas
        CREATE TABLE IF NOT EXISTS crm_vendas_conta (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(200) NOT NULL,
            cnpj VARCHAR(18),
            email VARCHAR(254),
            telefone VARCHAR(20),
            endereco TEXT,
            cidade VARCHAR(100),
            estado VARCHAR(2),
            cep VARCHAR(9),
            website VARCHAR(200),
            setor VARCHAR(100),
            numero_funcionarios INTEGER,
            receita_anual DECIMAL(15, 2),
            observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_conta_loja_idx ON crm_vendas_conta(loja_id);
        CREATE INDEX IF NOT EXISTS crm_conta_loja_cnpj_idx ON crm_vendas_conta(loja_id, cnpj);
        
        -- Tabela de Contatos
        CREATE TABLE IF NOT EXISTS crm_vendas_contato (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            conta_id INTEGER REFERENCES crm_vendas_conta(id) ON DELETE CASCADE,
            nome VARCHAR(200) NOT NULL,
            cargo VARCHAR(100),
            email VARCHAR(254),
            telefone VARCHAR(20),
            celular VARCHAR(20),
            data_nascimento DATE,
            observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_contato_loja_idx ON crm_vendas_contato(loja_id);
        CREATE INDEX IF NOT EXISTS crm_contato_conta_idx ON crm_vendas_contato(conta_id);
        
        -- Tabela de Leads
        CREATE TABLE IF NOT EXISTS crm_vendas_lead (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(200) NOT NULL,
            email VARCHAR(254),
            telefone VARCHAR(20),
            empresa VARCHAR(200),
            cargo VARCHAR(100),
            origem VARCHAR(50),
            status VARCHAR(50) DEFAULT 'novo',
            observacoes TEXT,
            vendedor_id INTEGER REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_lead_loja_idx ON crm_vendas_lead(loja_id);
        CREATE INDEX IF NOT EXISTS crm_lead_vendedor_idx ON crm_vendas_lead(vendedor_id);
        CREATE INDEX IF NOT EXISTS crm_lead_status_idx ON crm_vendas_lead(status);
        
        -- Tabela de Oportunidades
        CREATE TABLE IF NOT EXISTS crm_vendas_oportunidade (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(200) NOT NULL,
            conta_id INTEGER REFERENCES crm_vendas_conta(id) ON DELETE CASCADE,
            contato_id INTEGER REFERENCES crm_vendas_contato(id) ON DELETE SET NULL,
            vendedor_id INTEGER REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
            valor DECIMAL(15, 2),
            estagio VARCHAR(50) DEFAULT 'qualificacao',
            probabilidade INTEGER DEFAULT 0,
            data_fechamento_prevista DATE,
            data_fechamento_real DATE,
            origem VARCHAR(50),
            observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_opor_loja_idx ON crm_vendas_oportunidade(loja_id);
        CREATE INDEX IF NOT EXISTS crm_opor_conta_idx ON crm_vendas_oportunidade(conta_id);
        CREATE INDEX IF NOT EXISTS crm_opor_vendedor_idx ON crm_vendas_oportunidade(vendedor_id);
        CREATE INDEX IF NOT EXISTS crm_opor_estagio_idx ON crm_vendas_oportunidade(estagio);
        
        -- Tabela de Produtos/Serviços
        CREATE TABLE IF NOT EXISTS crm_vendas_produtoservico (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            nome VARCHAR(200) NOT NULL,
            codigo VARCHAR(50),
            descricao TEXT,
            preco DECIMAL(15, 2),
            custo DECIMAL(15, 2),
            tipo VARCHAR(20) DEFAULT 'produto',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_prod_loja_idx ON crm_vendas_produtoservico(loja_id);
        CREATE INDEX IF NOT EXISTS crm_prod_codigo_idx ON crm_vendas_produtoservico(codigo);
        
        -- Tabela de Propostas
        CREATE TABLE IF NOT EXISTS crm_vendas_proposta (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            numero VARCHAR(50) NOT NULL,
            oportunidade_id INTEGER REFERENCES crm_vendas_oportunidade(id) ON DELETE CASCADE,
            conta_id INTEGER REFERENCES crm_vendas_conta(id) ON DELETE CASCADE,
            vendedor_id INTEGER REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
            valor_total DECIMAL(15, 2),
            desconto DECIMAL(15, 2) DEFAULT 0,
            valor_final DECIMAL(15, 2),
            validade DATE,
            status VARCHAR(50) DEFAULT 'rascunho',
            observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_prop_loja_idx ON crm_vendas_proposta(loja_id);
        CREATE INDEX IF NOT EXISTS crm_prop_opor_idx ON crm_vendas_proposta(oportunidade_id);
        CREATE INDEX IF NOT EXISTS crm_prop_numero_idx ON crm_vendas_proposta(numero);
        
        -- Tabela de Itens da Proposta
        CREATE TABLE IF NOT EXISTS crm_vendas_itemproposta (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            proposta_id INTEGER REFERENCES crm_vendas_proposta(id) ON DELETE CASCADE,
            produto_servico_id INTEGER REFERENCES crm_vendas_produtoservico(id) ON DELETE CASCADE,
            quantidade DECIMAL(10, 2),
            preco_unitario DECIMAL(15, 2),
            desconto DECIMAL(15, 2) DEFAULT 0,
            valor_total DECIMAL(15, 2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_item_loja_idx ON crm_vendas_itemproposta(loja_id);
        CREATE INDEX IF NOT EXISTS crm_item_prop_idx ON crm_vendas_itemproposta(proposta_id);
        
        -- Tabela de Contratos
        CREATE TABLE IF NOT EXISTS crm_vendas_contrato (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            numero VARCHAR(50) NOT NULL,
            proposta_id INTEGER REFERENCES crm_vendas_proposta(id) ON DELETE SET NULL,
            conta_id INTEGER REFERENCES crm_vendas_conta(id) ON DELETE CASCADE,
            vendedor_id INTEGER REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
            valor_total DECIMAL(15, 2),
            data_inicio DATE,
            data_fim DATE,
            status VARCHAR(50) DEFAULT 'ativo',
            observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_contr_loja_idx ON crm_vendas_contrato(loja_id);
        CREATE INDEX IF NOT EXISTS crm_contr_numero_idx ON crm_vendas_contrato(numero);
        
        -- Tabela de Atividades
        CREATE TABLE IF NOT EXISTS crm_vendas_atividade (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            assunto VARCHAR(200) NOT NULL,
            descricao TEXT,
            data_hora TIMESTAMP WITH TIME ZONE,
            duracao INTEGER,
            status VARCHAR(50) DEFAULT 'agendada',
            conta_id INTEGER REFERENCES crm_vendas_conta(id) ON DELETE CASCADE,
            contato_id INTEGER REFERENCES crm_vendas_contato(id) ON DELETE SET NULL,
            oportunidade_id INTEGER REFERENCES crm_vendas_oportunidade(id) ON DELETE SET NULL,
            vendedor_id INTEGER REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_ativ_loja_idx ON crm_vendas_atividade(loja_id);
        CREATE INDEX IF NOT EXISTS crm_ativ_vendedor_idx ON crm_vendas_atividade(vendedor_id);
        CREATE INDEX IF NOT EXISTS crm_ativ_data_idx ON crm_vendas_atividade(data_hora);
        
        -- Tabela de Configurações
        CREATE TABLE IF NOT EXISTS crm_vendas_crmconfig (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL UNIQUE,
            moeda VARCHAR(3) DEFAULT 'BRL',
            formato_data VARCHAR(20) DEFAULT 'DD/MM/YYYY',
            fuso_horario VARCHAR(50) DEFAULT 'America/Sao_Paulo',
            meta_vendas_mensal DECIMAL(15, 2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_config_loja_idx ON crm_vendas_crmconfig(loja_id);
        
        -- Tabela de Assinaturas Digitais
        CREATE TABLE IF NOT EXISTS crm_vendas_assinaturadigital (
            id SERIAL PRIMARY KEY,
            loja_id INTEGER NOT NULL,
            proposta_id INTEGER REFERENCES crm_vendas_proposta(id) ON DELETE CASCADE,
            contrato_id INTEGER REFERENCES crm_vendas_contrato(id) ON DELETE CASCADE,
            signatario_nome VARCHAR(200),
            signatario_email VARCHAR(254),
            signatario_cpf VARCHAR(14),
            status VARCHAR(50) DEFAULT 'pendente',
            token VARCHAR(100),
            data_envio TIMESTAMP WITH TIME ZONE,
            data_assinatura TIMESTAMP WITH TIME ZONE,
            ip_assinatura VARCHAR(45),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crm_assin_loja_idx ON crm_vendas_assinaturadigital(loja_id);
        CREATE INDEX IF NOT EXISTS crm_assin_prop_idx ON crm_vendas_assinaturadigital(proposta_id);
        CREATE INDEX IF NOT EXISTS crm_assin_token_idx ON crm_vendas_assinaturadigital(token);
        """
        
        cursor.execute(sql)
        print(f"  ✅ Tabelas criadas com sucesso!")


def main():
    print("\n" + "="*80)
    print("CORRIGINDO TABELAS DO CRM NAS LOJAS")
    print("="*80 + "\n")
    
    # Buscar lojas CRM ativas
    lojas = Loja.objects.filter(
        tipo_loja__nome='CRM Vendas',
        is_active=True
    ).order_by('nome')
    
    if not lojas.exists():
        print("❌ Nenhuma loja CRM encontrada!")
        return
    
    print(f"📦 Encontradas {lojas.count()} lojas CRM\n")
    
    success_count = 0
    error_count = 0
    
    for loja in lojas:
        print(f"📦 Loja: {loja.nome} ({loja.database_name})")
        
        try:
            # Verificar se as tabelas já existem
            if check_crm_tables_exist(loja.database_name):
                print(f"  ℹ️  Tabelas já existem - pulando\n")
                success_count += 1
                continue
            
            # Criar tabelas
            create_crm_tables(loja.database_name)
            success_count += 1
            print()
            
        except Exception as e:
            print(f"  ❌ Erro: {e}\n")
            error_count += 1
    
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Erros: {error_count}")
    print(f"📊 Total: {lojas.count()}")
    print()


if __name__ == '__main__':
    main()
