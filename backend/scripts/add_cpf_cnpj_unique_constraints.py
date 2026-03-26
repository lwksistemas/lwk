#!/usr/bin/env python
"""
Script para adicionar constraints únicos de CPF/CNPJ nos modelos de clientes/pacientes.
Previne cadastros duplicados por loja.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection


def add_unique_constraints():
    """Adiciona constraints únicos de CPF/CNPJ nas tabelas."""
    
    print("\n" + "="*80)
    print("ADICIONANDO CONSTRAINTS ÚNICOS DE CPF/CNPJ")
    print("="*80 + "\n")
    
    # Lista de tabelas e campos para adicionar constraint
    constraints = [
        # CRM Vendas - Conta (CNPJ)
        {
            'schema': 'loja_%',  # Aplicar em todos os schemas de loja
            'table': 'crm_vendas_conta',
            'column': 'cnpj',
            'constraint_name': 'unique_conta_cnpj_per_loja',
            'description': 'CRM Vendas - Conta (CNPJ único por loja)'
        },
        # Clínica Estética - Cliente (CPF)
        {
            'schema': 'loja_%',
            'table': 'clinica_estetica_cliente',
            'column': 'cpf',
            'constraint_name': 'unique_cliente_cpf_per_loja',
            'description': 'Clínica Estética - Cliente (CPF único por loja)'
        },
        # Restaurante - Cliente (CPF/CNPJ)
        {
            'schema': 'loja_%',
            'table': 'restaurante_cliente',
            'column': 'cpf_cnpj',
            'constraint_name': 'unique_cliente_cpf_cnpj_per_loja',
            'description': 'Restaurante - Cliente (CPF/CNPJ único por loja)'
        },
        # E-commerce - Cliente (CPF/CNPJ)
        {
            'schema': 'loja_%',
            'table': 'ecommerce_cliente',
            'column': 'cpf_cnpj',
            'constraint_name': 'unique_ecommerce_cliente_cpf_cnpj_per_loja',
            'description': 'E-commerce - Cliente (CPF/CNPJ único por loja)'
        },
    ]
    
    with connection.cursor() as cursor:
        # Buscar todos os schemas de loja
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'loja_%'
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        
        print(f"📦 Encontrados {len(schemas)} schemas de loja\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for schema in schemas:
            print(f"📦 Schema: {schema}")
            
            for constraint in constraints:
                table = constraint['table']
                column = constraint['column']
                constraint_name = constraint['constraint_name']
                description = constraint['description']
                
                try:
                    # Verificar se a tabela existe
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s
                            AND table_name = %s
                        )
                    """, [schema, table])
                    
                    table_exists = cursor.fetchone()[0]
                    
                    if not table_exists:
                        print(f"  ⏭️  Tabela {table} não existe - pulando")
                        skip_count += 1
                        continue
                    
                    # Verificar se a coluna existe
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = %s
                            AND table_name = %s
                            AND column_name = %s
                        )
                    """, [schema, table, column])
                    
                    column_exists = cursor.fetchone()[0]
                    
                    if not column_exists:
                        print(f"  ⏭️  Coluna {column} não existe em {table} - pulando")
                        skip_count += 1
                        continue
                    
                    # Verificar se já existe constraint
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM pg_constraint 
                            WHERE conname = %s
                            AND connamespace = (
                                SELECT oid FROM pg_namespace WHERE nspname = %s
                            )
                        )
                    """, [constraint_name, schema])
                    
                    constraint_exists = cursor.fetchone()[0]
                    
                    if constraint_exists:
                        print(f"  ℹ️  Constraint {constraint_name} já existe - pulando")
                        skip_count += 1
                        continue
                    
                    # Verificar se há duplicatas antes de adicionar constraint
                    cursor.execute(f"""
                        SET search_path TO {schema};
                        SELECT {column}, COUNT(*) as count
                        FROM {table}
                        WHERE {column} IS NOT NULL AND {column} != ''
                        GROUP BY {column}
                        HAVING COUNT(*) > 1
                    """)
                    
                    duplicates = cursor.fetchall()
                    
                    if duplicates:
                        print(f"  ⚠️  ATENÇÃO: Encontradas {len(duplicates)} duplicatas em {table}.{column}:")
                        for dup in duplicates[:5]:  # Mostrar apenas as primeiras 5
                            print(f"      - {dup[0]}: {dup[1]} registros")
                        print(f"  ❌ Não é possível adicionar constraint com duplicatas existentes")
                        print(f"  💡 Resolva as duplicatas manualmente antes de adicionar o constraint")
                        error_count += 1
                        continue
                    
                    # Adicionar constraint
                    cursor.execute(f"""
                        SET search_path TO {schema};
                        ALTER TABLE {table}
                        ADD CONSTRAINT {constraint_name}
                        UNIQUE (loja_id, {column})
                        WHERE {column} IS NOT NULL AND {column} != ''
                    """)
                    
                    print(f"  ✅ Constraint {constraint_name} adicionado em {table}.{column}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Erro ao processar {table}.{column}: {e}")
                    error_count += 1
            
            print()  # Linha em branco entre schemas
    
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"✅ Sucesso: {success_count}")
    print(f"⏭️  Pulados: {skip_count}")
    print(f"❌ Erros: {error_count}")
    print()


if __name__ == '__main__':
    add_unique_constraints()
