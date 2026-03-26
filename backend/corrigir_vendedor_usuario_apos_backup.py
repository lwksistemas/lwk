#!/usr/bin/env python
"""
Script para corrigir VendedorUsuario após importação de backup.
Quando um backup é importado, os vendedores são recriados no schema isolado
com novos IDs, mas o VendedorUsuario ainda aponta para os IDs antigos.

Este script atualiza o VendedorUsuario para apontar para o vendedor correto
baseado no email.

Versão: v1365
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwksistemas.settings')
django.setup()

from django.contrib.auth import get_user_model
from superadmin.models import Loja, VendedorUsuario
from crm_vendas.models import Vendedor
from tenants.middleware import set_current_loja_id

User = get_user_model()

def corrigir_vendedor_usuario(loja_slug_ou_cnpj):
    """
    Corrige VendedorUsuario para apontar para o vendedor correto após backup.
    
    Args:
        loja_slug_ou_cnpj: Slug ou CNPJ da loja
    """
    # Buscar loja
    loja = Loja.objects.filter(slug=loja_slug_ou_cnpj).first()
    if not loja:
        loja = Loja.objects.filter(cpf_cnpj=loja_slug_ou_cnpj).first()
    
    if not loja:
        print(f"❌ Loja não encontrada: {loja_slug_ou_cnpj}")
        return
    
    print(f"\n{'='*80}")
    print(f"CORRIGIR VENDEDOR USUARIO APÓS BACKUP")
    print(f"{'='*80}\n")
    print(f"Loja: {loja.nome} (ID: {loja.id})")
    print(f"Owner: {loja.owner.username} ({loja.owner.email})\n")
    
    # Setar contexto
    set_current_loja_id(loja.id)
    
    # Buscar todos os VendedorUsuario da loja
    vendedor_usuarios = VendedorUsuario.objects.using('default').filter(loja_id=loja.id)
    
    print(f"Total de VendedorUsuario encontrados: {vendedor_usuarios.count()}\n")
    
    corrigidos = 0
    erros = 0
    
    for vu in vendedor_usuarios:
        print(f"VendedorUsuario ID={vu.id}:")
        print(f"  - User: {vu.user.username} ({vu.user.email})")
        print(f"  - Vendedor ID antigo: {vu.vendedor_id}")
        
        # Verificar se vendedor existe no schema isolado
        vendedor_existe = Vendedor.objects.filter(id=vu.vendedor_id).exists()
        
        if vendedor_existe:
            print(f"  ✅ Vendedor ID={vu.vendedor_id} existe no schema")
            continue
        
        print(f"  ❌ Vendedor ID={vu.vendedor_id} NÃO existe no schema")
        
        # Buscar vendedor pelo email do usuário
        vendedor_correto = Vendedor.objects.filter(
            email__iexact=vu.user.email
        ).first()
        
        if vendedor_correto:
            print(f"  ✅ Vendedor encontrado pelo email: ID={vendedor_correto.id}, Nome={vendedor_correto.nome}")
            
            # Atualizar VendedorUsuario
            vu.vendedor_id = vendedor_correto.id
            vu.save(update_fields=['vendedor_id'])
            
            print(f"  ✅ VendedorUsuario atualizado: vendedor_id={vu.vendedor_id}")
            corrigidos += 1
        else:
            print(f"  ❌ Vendedor não encontrado pelo email: {vu.user.email}")
            erros += 1
        
        print()
    
    print(f"{'='*80}")
    print(f"RESUMO")
    print(f"{'='*80}")
    print(f"Total: {vendedor_usuarios.count()}")
    print(f"Corrigidos: {corrigidos}")
    print(f"Erros: {erros}")
    print(f"Já corretos: {vendedor_usuarios.count() - corrigidos - erros}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python backend/corrigir_vendedor_usuario_apos_backup.py <slug_ou_cnpj>")
        print("Exemplo: python backend/corrigir_vendedor_usuario_apos_backup.py 41449198000172")
        sys.exit(1)
    
    corrigir_vendedor_usuario(sys.argv[1])
