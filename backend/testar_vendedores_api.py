#!/usr/bin/env python
"""
Script para testar o endpoint de vendedores e debug do contexto
Versão: v1355
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwksistemas.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from superadmin.models import Loja
from crm_vendas.views import VendedorViewSet
from tenants.middleware import get_current_loja_id, set_current_loja_id
from crm_vendas.models import Vendedor

User = get_user_model()

def testar():
    # Buscar loja
    loja = Loja.objects.get(cpf_cnpj='41.449.198/0001-72')
    print(f"\n{'='*80}")
    print(f"TESTE DO ENDPOINT DE VENDEDORES")
    print(f"{'='*80}\n")
    print(f"Loja: {loja.nome} (ID: {loja.id})")
    print(f"Schema: {loja.database_name}")
    print(f"Owner: {loja.owner.username}\n")
    
    # Setar contexto manualmente
    set_current_loja_id(loja.id)
    print(f"✅ Contexto setado: loja_id={get_current_loja_id()}\n")
    
    # Testar queryset diretamente
    print(f"{'='*80}")
    print(f"TESTE 1: Queryset direto (sem filtro)")
    print(f"{'='*80}")
    from django.db import connections
    with connections['default'].cursor() as cursor:
        cursor.execute(f"""
            SET search_path TO {loja.database_name}, public;
            SELECT id, nome, email, is_admin, is_active, loja_id
            FROM crm_vendas_vendedor;
        """)
        vendedores = cursor.fetchall()
        print(f"Total no banco: {len(vendedores)}")
        for v in vendedores:
            print(f"  - ID: {v[0]}, Nome: {v[1]}, Email: {v[2]}, is_admin: {v[3]}, is_active: {v[4]}, loja_id: {v[5]}")
    
    print(f"\n{'='*80}")
    print(f"TESTE 2: Vendedor.objects.all() (com LojaIsolationManager)")
    print(f"{'='*80}")
    print(f"Contexto atual: loja_id={get_current_loja_id()}")
    vendedores_qs = Vendedor.objects.all()
    print(f"Total no queryset: {vendedores_qs.count()}")
    for v in vendedores_qs:
        print(f"  - ID: {v.id}, Nome: {v.nome}, Email: {v.email}, is_admin: {v.is_admin}, loja_id: {v.loja_id}")
    
    print(f"\n{'='*80}")
    print(f"TESTE 3: VendedorViewSet.get_queryset()")
    print(f"{'='*80}")
    factory = RequestFactory()
    request = factory.get(
        '/api/crm-vendas/vendedores/',
        HTTP_X_LOJA_ID=str(loja.id),
        HTTP_X_TENANT_SLUG=loja.slug
    )
    request.user = loja.owner
    
    # Setar contexto novamente (pode ter sido limpo)
    set_current_loja_id(loja.id)
    print(f"Contexto antes do viewset: loja_id={get_current_loja_id()}")
    
    viewset = VendedorViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    viewset.action = 'list'
    
    qs = viewset.get_queryset()
    print(f"Contexto depois do viewset: loja_id={get_current_loja_id()}")
    print(f"Total no viewset queryset: {qs.count()}")
    for v in qs:
        print(f"  - ID: {v.id}, Nome: {v.nome}, Email: {v.email}, is_admin: {v.is_admin}")
    
    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO")
    print(f"{'='*80}")
    if vendedores_qs.count() == 0:
        print(f"❌ PROBLEMA: LojaIsolationManager está filtrando tudo")
        print(f"   Contexto loja_id: {get_current_loja_id()}")
        print(f"   Loja esperada: {loja.id}")
        print(f"   Vendedor loja_id no banco: {vendedores[0][5] if vendedores else 'N/A'}")
    else:
        print(f"✅ Queryset funcionando corretamente")
    
    print(f"{'='*80}\n")

if __name__ == '__main__':
    testar()
