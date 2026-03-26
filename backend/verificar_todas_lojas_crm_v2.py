#!/usr/bin/env python
"""
Script para verificar vendedores admin em todas as lojas CRM Vendas
Versão: v1351 - Usando SQL direto
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwksistemas.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def main():
    # Buscar lojas CRM Vendas
    lojas_crm = Loja.objects.filter(tipo_loja__nome='CRM Vendas')
    
    print(f"\n{'='*80}")
    print(f"VERIFICAÇÃO DE VENDEDORES ADMIN - CRM VENDAS")
    print(f"{'='*80}\n")
    print(f"Total de lojas CRM Vendas: {lojas_crm.count()}\n")
    
    total_ok = 0
    total_problemas = 0
    
    for loja in lojas_crm:
        print(f"{'='*80}")
        print(f"Loja: {loja.nome}")
        print(f"CPF/CNPJ: {loja.cpf_cnpj}")
        print(f"Tipo: {loja.tipo_loja.nome}")
        print(f"Schema: {loja.database_name}")
        print(f"Owner: {loja.owner.username if loja.owner else 'SEM OWNER'}")
        
        if not loja.owner:
            print(f"❌ PROBLEMA: Loja sem owner!")
            total_problemas += 1
            print()
            continue
        
        # Buscar vendedor do owner usando SQL direto
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SET search_path TO {loja.database_name}, public;
                SELECT id, nome, email, is_admin
                FROM crm_vendas_vendedor
                WHERE usuario_id = %s;
            """, [loja.owner.id])
            
            vendedor = cursor.fetchone()
            
            if vendedor:
                vendedor_id, nome, email, is_admin = vendedor
                print(f"✅ Vendedor encontrado:")
                print(f"   - ID: {vendedor_id}")
                print(f"   - Nome: {nome}")
                print(f"   - Email: {email}")
                print(f"   - is_admin: {is_admin}")
                
                if is_admin:
                    print(f"✅ CONFIGURAÇÃO CORRETA - Owner é admin!")
                    total_ok += 1
                else:
                    print(f"⚠️  ATENÇÃO: Vendedor existe mas is_admin=False")
                    total_problemas += 1
            else:
                print(f"❌ PROBLEMA: Nenhum vendedor encontrado para o owner!")
                total_problemas += 1
        
        print()
    
    print(f"{'='*80}")
    print(f"RESUMO DA VERIFICAÇÃO")
    print(f"{'='*80}")
    print(f"Total de lojas: {lojas_crm.count()}")
    print(f"✅ Lojas OK: {total_ok}")
    print(f"❌ Lojas com problemas: {total_problemas}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
