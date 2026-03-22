#!/usr/bin/env python
"""
Script para verificar se o owner da loja tem VendedorUsuario vinculado.
Isso pode causar o problema de perfil intermitente.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from superadmin.models import Loja, VendedorUsuario
from crm_vendas.models import Vendedor

def check_owner_vendedor(cpf_cnpj):
    """Verifica se owner tem VendedorUsuario vinculado."""
    print(f"\n{'='*60}")
    print(f"🔍 VERIFICANDO LOJA: {cpf_cnpj}")
    print(f"{'='*60}\n")
    
    # Buscar loja
    try:
        loja = Loja.objects.using('default').select_related('owner').get(cpf_cnpj=cpf_cnpj)
    except Loja.DoesNotExist:
        print(f"❌ ERRO: Loja com CPF/CNPJ {cpf_cnpj} não encontrada")
        return
    
    owner = loja.owner
    
    print(f"✅ Loja encontrada:")
    print(f"   Nome: {loja.nome}")
    print(f"   ID: {loja.id}")
    print(f"   Slug: {loja.slug}")
    print(f"\n✅ Owner:")
    print(f"   Username: {owner.username}")
    print(f"   Email: {owner.email}")
    print(f"   ID: {owner.id}")
    print(f"   Owner ID da loja: {loja.owner_id}")
    
    # Verificar se owner tem VendedorUsuario
    print(f"\n{'='*60}")
    print(f"🔍 VERIFICANDO VendedorUsuario")
    print(f"{'='*60}\n")
    
    vu_list = VendedorUsuario.objects.using('default').filter(
        user=owner,
        loja=loja
    ).select_related('loja')
    
    if vu_list.exists():
        print(f"❌ PROBLEMA ENCONTRADO: Owner tem {vu_list.count()} VendedorUsuario(s) vinculado(s)!\n")
        
        for vu in vu_list:
            print(f"   VendedorUsuario ID: {vu.id}")
            print(f"   Vendedor ID: {vu.vendedor_id}")
            print(f"   Precisa trocar senha: {vu.precisa_trocar_senha}")
            print(f"   Criado em: {vu.created_at}")
            
            # Buscar dados do vendedor
            try:
                # Usar o database da loja
                from django.db import connections
                from tenants.middleware import set_current_loja_id
                
                set_current_loja_id(loja.id)
                vendedor = Vendedor.objects.filter(id=vu.vendedor_id).first()
                
                if vendedor:
                    print(f"   Vendedor Nome: {vendedor.nome}")
                    print(f"   Vendedor Email: {vendedor.email}")
                    print(f"   Vendedor is_admin: {vendedor.is_admin}")
                else:
                    print(f"   ⚠️ Vendedor não encontrado no banco da loja")
            except Exception as e:
                print(f"   ⚠️ Erro ao buscar vendedor: {e}")
            
            print()
        
        print(f"\n{'='*60}")
        print(f"🔧 SOLUÇÃO RECOMENDADA")
        print(f"{'='*60}\n")
        print(f"Execute o seguinte comando para remover VendedorUsuario do owner:\n")
        print(f"from superadmin.models import Loja, VendedorUsuario")
        print(f"loja = Loja.objects.get(cpf_cnpj='{cpf_cnpj}')")
        print(f"VendedorUsuario.objects.filter(user=loja.owner, loja=loja).delete()")
        print(f"\nOu execute: python fix_owner_vendedor.py {cpf_cnpj}\n")
        
    else:
        print(f"✅ OK: Owner NÃO tem VendedorUsuario vinculado")
        print(f"\nO problema pode ser causado por:")
        print(f"1. Cache do sessionStorage no navegador")
        print(f"2. Sessão antiga ainda ativa")
        print(f"3. Race condition no frontend")
        print(f"\nSoluções:")
        print(f"1. Limpar sessionStorage no navegador (DevTools → Application)")
        print(f"2. Fazer logout e login novamente")
        print(f"3. Limpar cookies e cache do navegador")
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    cpf_cnpj = '41449198000172'
    check_owner_vendedor(cpf_cnpj)
