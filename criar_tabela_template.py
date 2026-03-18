#!/usr/bin/env python
"""Script para criar a tabela de templates de propostas no Heroku."""

from django.db import connection

# SQL para criar a tabela
sql = """
CREATE TABLE IF NOT EXISTS crm_vendas_proposta_template (
    id BIGSERIAL PRIMARY KEY,
    loja_id INTEGER NOT NULL,
    nome VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    is_padrao BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Criar índices
CREATE INDEX IF NOT EXISTS crm_pt_loja_ativo_idx ON crm_vendas_proposta_template (loja_id, ativo);
CREATE INDEX IF NOT EXISTS crm_pt_loja_padrao_idx ON crm_vendas_proposta_template (loja_id, is_padrao);
CREATE INDEX IF NOT EXISTS crm_vendas_proposta_template_loja_id_idx ON crm_vendas_proposta_template (loja_id);
"""

print("Criando tabela crm_vendas_proposta_template...")
with connection.cursor() as cursor:
    cursor.execute(sql)
    print("✅ Tabela criada com sucesso!")

# Verificar se a tabela foi criada
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name = 'crm_vendas_proposta_template'
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"✅ Tabela existe! Total de registros: {count}")
    else:
        print("❌ Tabela não foi criada")

# Verificar estrutura
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'crm_vendas_proposta_template'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print("\n📋 Estrutura da tabela:")
    for col_name, col_type in columns:
        print(f"  - {col_name}: {col_type}")
