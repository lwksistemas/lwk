#!/usr/bin/env python
"""
Script para verificar vendedores admin em todas as lojas CRM Vendas
Versão: v1348
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwksistemas.settings')
django.setup()

from django_tenants.utils import schema_context
from superadmin.models import Loja
from crm_vendas.models import Vendedor

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
        
        # Conectar ao schema da loja usando context manager
        with schema_context(loja.database_name):
            # Buscar vendedor do owner
            vendedores = Vendedor.objects.filter(usuario=loja.owner)
            
            if vendedores.exists():
                vendedor = vendedores.first()
                print(f"✅ Vendedor encontrado:")
                print(f"   - ID: {vendedor.id}")
                print(f"   - Nome: {vendedor.nome}")
                print(f"   - Email: {vendedor.email}")
                print(f"   - is_admin: {vendedor.is_admin}")
                print(f"   - Ativo: {vendedor.ativo}")
                
                if vendedor.is_admin:
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
