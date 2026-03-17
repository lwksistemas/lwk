#!/usr/bin/env python
"""
Script para verificar constraint de foreign key em FinanceiroLoja
Identifica se a constraint está configurada corretamente com CASCADE
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection


def verificar_constraint_financeiro():
    """Verifica constraint de foreign key em superadmin_financeiroloja"""
    
    print("\n" + "="*80)
    print("VERIFICAÇÃO DE CONSTRAINT: superadmin_financeiroloja")
    print("="*80 + "\n")
    
    with connection.cursor() as cursor:
        # Buscar informações da constraint
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.table_name = 'superadmin_financeiroloja'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'loja_id';
        """)
        
        result = cursor.fetchone()
        
        if not result:
            print("❌ ERRO: Constraint não encontrada!")
            print("   Tabela: superadmin_financeiroloja")
            print("   Coluna: loja_id")
            return False
        
        constraint_name, table_name, column_name, foreign_table, foreign_column, update_rule, delete_rule = result
        
        print(f"✅ Constraint encontrada:")
        print(f"   Nome: {constraint_name}")
        print(f"   Tabela: {table_name}")
        print(f"   Coluna: {column_name}")
        print(f"   Referencia: {foreign_table}.{foreign_column}")
        print(f"   Update Rule: {update_rule}")
        print(f"   Delete Rule: {delete_rule}")
        print()
        
        # Verificar se está correto
        if delete_rule == 'CASCADE':
            print("✅ DELETE RULE está correto: CASCADE")
            print("   A exclusão da loja deve excluir automaticamente o financeiro.")
        else:
            print(f"❌ DELETE RULE está INCORRETO: {delete_rule}")
            print("   Deveria ser: CASCADE")
            print("   Isso impede a exclusão de lojas!")
            print()
            print("🔧 SOLUÇÃO:")
            print("   1. Criar migration para corrigir a constraint")
            print("   2. Ou executar SQL manualmente:")
            print()
            print(f"   ALTER TABLE superadmin_financeiroloja")
            print(f"   DROP CONSTRAINT {constraint_name};")
            print()
            print(f"   ALTER TABLE superadmin_financeiroloja")
            print(f"   ADD CONSTRAINT {constraint_name}")
            print(f"   FOREIGN KEY (loja_id)")
            print(f"   REFERENCES superadmin_loja(id)")
            print(f"   ON DELETE CASCADE")
            print(f"   DEFERRABLE INITIALLY DEFERRED;")
            return False
        
        print()
        
        # Verificar lojas problemáticas
        print("-" * 80)
        print("VERIFICANDO LOJAS PROBLEMÁTICAS:")
        print("-" * 80)
        print()
        
        cursor.execute("""
            SELECT 
                l.id, 
                l.slug, 
                l.nome,
                f.id as financeiro_id,
                f.status_pagamento
            FROM superadmin_loja l
            LEFT JOIN superadmin_financeiroloja f ON l.id = f.loja_id
            WHERE l.slug IN ('felix-5889', 'harmonis-000126', 'vida-1845')
            ORDER BY l.id;
        """)
        
        lojas = cursor.fetchall()
        
        if not lojas:
            print("ℹ️  Nenhuma loja problemática encontrada")
        else:
            for loja_id, slug, nome, financeiro_id, status in lojas:
                print(f"Loja ID: {loja_id}")
                print(f"  Slug: {slug}")
                print(f"  Nome: {nome}")
                print(f"  Financeiro ID: {financeiro_id}")
                print(f"  Status Pagamento: {status}")
                print()
        
        return True


if __name__ == '__main__':
    try:
        verificar_constraint_financeiro()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
