#!/usr/bin/env python
"""Script para adicionar colunas na tabela de funcionários"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def add_columns():
    with connection.cursor() as cursor:
        print("🔧 Adicionando colunas na tabela cabeleireiro_funcionarios...")
        
        # Adicionar coluna funcao
        try:
            cursor.execute("""
                ALTER TABLE cabeleireiro_funcionarios 
                ADD COLUMN IF NOT EXISTS funcao VARCHAR(20) DEFAULT 'atendente';
            """)
            print("✅ Coluna 'funcao' adicionada/verificada")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar 'funcao': {e}")
        
        # Adicionar coluna especialidade
        try:
            cursor.execute("""
                ALTER TABLE cabeleireiro_funcionarios 
                ADD COLUMN IF NOT EXISTS especialidade VARCHAR(100);
            """)
            print("✅ Coluna 'especialidade' adicionada/verificada")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar 'especialidade': {e}")
        
        # Adicionar coluna comissao_percentual
        try:
            cursor.execute("""
                ALTER TABLE cabeleireiro_funcionarios 
                ADD COLUMN IF NOT EXISTS comissao_percentual NUMERIC(5,2) DEFAULT 0.00;
            """)
            print("✅ Coluna 'comissao_percentual' adicionada/verificada")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar 'comissao_percentual': {e}")
        
        print("\n✅ Script concluído com sucesso!")

if __name__ == '__main__':
    add_columns()
