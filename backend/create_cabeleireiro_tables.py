#!/usr/bin/env python
"""Script para criar tabelas do cabeleireiro no banco de lojas"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from django.core.management import call_command

def create_tables():
    print("🔧 Criando tabelas do cabeleireiro no banco de lojas...")
    
    # Usar o banco 'lojas'
    connection = connections['lojas']
    
    with connection.cursor() as cursor:
        # Criar tabela de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_clientes (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                nome VARCHAR(200) NOT NULL,
                email VARCHAR(254),
                telefone VARCHAR(20) NOT NULL,
                cpf VARCHAR(14),
                data_nascimento DATE,
                endereco TEXT,
                cidade VARCHAR(100),
                estado VARCHAR(2),
                observacoes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_clientes criada")
        
        # Criar tabela de profissionais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_profissionais (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                nome VARCHAR(200) NOT NULL,
                email VARCHAR(254),
                telefone VARCHAR(20) NOT NULL,
                especialidade VARCHAR(100),
                comissao_percentual NUMERIC(5,2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_profissionais criada")
        
        # Criar tabela de serviços
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_servicos (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                nome VARCHAR(200) NOT NULL,
                descricao TEXT,
                categoria VARCHAR(20) NOT NULL,
                duracao INTEGER NOT NULL,
                preco NUMERIC(10,2) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_servicos criada")
        
        # Criar tabela de agendamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_agendamentos (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                cliente_id INTEGER NOT NULL REFERENCES cabeleireiro_clientes(id) ON DELETE CASCADE,
                profissional_id INTEGER REFERENCES cabeleireiro_profissionais(id) ON DELETE SET NULL,
                servico_id INTEGER NOT NULL REFERENCES cabeleireiro_servicos(id) ON DELETE CASCADE,
                data DATE NOT NULL,
                horario TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'agendado',
                observacoes TEXT,
                valor NUMERIC(10,2) NOT NULL,
                valor_pago NUMERIC(10,2) DEFAULT 0.00,
                forma_pagamento VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_agendamentos criada")
        
        # Criar tabela de produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_produtos (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                nome VARCHAR(200) NOT NULL,
                descricao TEXT,
                categoria VARCHAR(20) NOT NULL,
                marca VARCHAR(100),
                preco_custo NUMERIC(10,2) NOT NULL,
                preco_venda NUMERIC(10,2) NOT NULL,
                estoque_atual INTEGER DEFAULT 0,
                estoque_minimo INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_produtos criada")
        
        # Criar tabela de vendas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_vendas (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                cliente_id INTEGER REFERENCES cabeleireiro_clientes(id) ON DELETE SET NULL,
                produto_id INTEGER NOT NULL REFERENCES cabeleireiro_produtos(id) ON DELETE CASCADE,
                quantidade INTEGER NOT NULL,
                valor_unitario NUMERIC(10,2) NOT NULL,
                valor_total NUMERIC(10,2) NOT NULL,
                forma_pagamento VARCHAR(20) NOT NULL,
                data_venda TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                observacoes TEXT
            );
        """)
        print("✅ Tabela cabeleireiro_vendas criada")
        
        # Criar tabela de funcionários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_funcionarios (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                nome VARCHAR(200) NOT NULL,
                email VARCHAR(254),
                telefone VARCHAR(20) NOT NULL,
                cpf VARCHAR(14),
                cargo VARCHAR(100) NOT NULL,
                funcao VARCHAR(20) DEFAULT 'atendente',
                especialidade VARCHAR(100),
                comissao_percentual NUMERIC(5,2) DEFAULT 0.00,
                salario NUMERIC(10,2),
                data_admissao DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabela cabeleireiro_funcionarios criada")
        
        # Criar tabela de horários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_horarios (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                dia_semana INTEGER NOT NULL,
                horario_abertura TIME NOT NULL,
                horario_fechamento TIME NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        print("✅ Tabela cabeleireiro_horarios criada")
        
        # Criar tabela de bloqueios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cabeleireiro_bloqueios (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                profissional_id INTEGER NOT NULL REFERENCES cabeleireiro_profissionais(id) ON DELETE CASCADE,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                motivo VARCHAR(200) NOT NULL,
                observacoes TEXT
            );
        """)
        print("✅ Tabela cabeleireiro_bloqueios criada")
        
        print("\n✅ Todas as tabelas do cabeleireiro foram criadas com sucesso!")

if __name__ == '__main__':
    create_tables()
