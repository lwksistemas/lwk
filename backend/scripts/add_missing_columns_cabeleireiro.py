#!/usr/bin/env python
"""
Script para adicionar colunas faltantes na tabela cabeleireiro_funcionarios.
Uso: heroku run python backend/scripts/add_missing_columns_cabeleireiro.py --app lwksistemas
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def main():
    # Buscar todas as lojas de cabeleireiro
    lojas_cabeleireiro = Loja.objects.filter(tipo_loja__nome__icontains='cabeleireiro')
    
    print(f'Encontradas {lojas_cabeleireiro.count()} lojas de cabeleireiro')
    
    for loja in lojas_cabeleireiro:
        print(f'\n📍 Processando loja: {loja.nome} (ID: {loja.id}, Slug: {loja.slug})')
        
        try:
            # Conectar ao schema da loja
            schema_name = f'loja_{loja.slug.replace("-", "_")}'
            
            with connection.cursor() as cursor:
                # Setar o search_path para o schema da loja
                cursor.execute(f'SET search_path TO {schema_name}, public')
                
                # Verificar se a tabela existe
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_funcionarios'
                """, [schema_name])
                
                if not cursor.fetchone():
                    print(f'  ⚠️  Tabela cabeleireiro_funcionarios não existe no schema {schema_name}')
                    continue
                
                # Verificar quais colunas existem
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_funcionarios'
                """, [schema_name])
                
                existing_columns = [row[0] for row in cursor.fetchall()]
                print(f'  📋 Colunas existentes: {", ".join(existing_columns)}')
                
                # Adicionar coluna cpf se não existir
                if 'cpf' not in existing_columns:
                    print('  ➕ Adicionando coluna cpf...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_funcionarios 
                        ADD COLUMN cpf VARCHAR(14)
                    """)
                    print('  ✅ Coluna cpf adicionada')
                else:
                    print('  ✓ Coluna cpf já existe')
                
                # Adicionar coluna salario se não existir
                if 'salario' not in existing_columns:
                    print('  ➕ Adicionando coluna salario...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_funcionarios 
                        ADD COLUMN salario DECIMAL(10,2)
                    """)
                    print('  ✅ Coluna salario adicionada')
                else:
                    print('  ✓ Coluna salario já existe')
                
                # Adicionar colunas de endereço e cidade/estado nos clientes se não existirem
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_clientes'
                """, [schema_name])
                
                cliente_columns = [row[0] for row in cursor.fetchall()]
                
                if 'endereco' not in cliente_columns:
                    print('  ➕ Adicionando coluna endereco em clientes...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_clientes 
                        ADD COLUMN endereco TEXT
                    """)
                    print('  ✅ Coluna endereco adicionada')
                
                if 'cidade' not in cliente_columns:
                    print('  ➕ Adicionando coluna cidade em clientes...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_clientes 
                        ADD COLUMN cidade VARCHAR(100)
                    """)
                    print('  ✅ Coluna cidade adicionada')
                
                if 'estado' not in cliente_columns:
                    print('  ➕ Adicionando coluna estado em clientes...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_clientes 
                        ADD COLUMN estado VARCHAR(2)
                    """)
                    print('  ✅ Coluna estado adicionada')
                
                # Ajustar colunas de agendamentos
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_agendamentos'
                """, [schema_name])
                
                agendamento_columns = [row[0] for row in cursor.fetchall()]
                
                if 'valor' not in agendamento_columns:
                    print('  ➕ Adicionando coluna valor em agendamentos...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_agendamentos 
                        ADD COLUMN valor DECIMAL(10,2) DEFAULT 0.00
                    """)
                    print('  ✅ Coluna valor adicionada')
                
                if 'forma_pagamento' not in agendamento_columns:
                    print('  ➕ Adicionando coluna forma_pagamento em agendamentos...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_agendamentos 
                        ADD COLUMN forma_pagamento VARCHAR(50)
                    """)
                    print('  ✅ Coluna forma_pagamento adicionada')
                
                # Ajustar colunas de produtos
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_produtos'
                """, [schema_name])
                
                produto_columns = [row[0] for row in cursor.fetchall()]
                
                if 'marca' not in produto_columns:
                    print('  ➕ Adicionando coluna marca em produtos...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_produtos 
                        ADD COLUMN marca VARCHAR(100)
                    """)
                    print('  ✅ Coluna marca adicionada')
                
                # Ajustar colunas de vendas
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_vendas'
                """, [schema_name])
                
                venda_columns = [row[0] for row in cursor.fetchall()]
                
                if 'observacoes' not in venda_columns:
                    print('  ➕ Adicionando coluna observacoes em vendas...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_vendas 
                        ADD COLUMN observacoes TEXT
                    """)
                    print('  ✅ Coluna observacoes adicionada')
                
                # Ajustar colunas de bloqueios
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'cabeleireiro_bloqueioagenda'
                """, [schema_name])
                
                bloqueio_columns = [row[0] for row in cursor.fetchall()]
                
                if 'observacoes' not in bloqueio_columns:
                    print('  ➕ Adicionando coluna observacoes em bloqueios...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_bloqueioagenda 
                        ADD COLUMN observacoes TEXT
                    """)
                    print('  ✅ Coluna observacoes adicionada')
                
                if 'is_active' not in bloqueio_columns:
                    print('  ➕ Adicionando coluna is_active em bloqueios...')
                    cursor.execute("""
                        ALTER TABLE cabeleireiro_bloqueioagenda 
                        ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                    """)
                    print('  ✅ Coluna is_active adicionada')
                
                # Resetar search_path
                cursor.execute('SET search_path TO public')
                
                print(f'  ✅ Schema {schema_name} atualizado com sucesso!')
                
        except Exception as e:
            print(f'  ❌ Erro: {str(e)}')
            import traceback
            traceback.print_exc()
    
    print('\n✅ Processo concluído!')

if __name__ == '__main__':
    main()
