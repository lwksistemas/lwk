#!/usr/bin/env python
"""
Script para testar a API HTTP completa (simulando requisição do frontend)
Versão: v1359
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
from tenants.middleware import TenantMiddleware
from rest_framework.test import force_authenticate

User = get_user_model()

def testar():
    # Buscar loja
    loja = Loja.objects.get(cpf_cnpj='41.449.198/0001-72')
    print(f"\n{'='*80}")
    print(f"TESTE DA API HTTP COMPLETA")
    print(f"{'='*80}\n")
    print(f"Loja: {loja.nome} (ID: {loja.id})")
    print(f"Owner: {loja.owner.username} ({loja.owner.email})\n")
    
    # Criar requisição HTTP simulada
    factory = RequestFactory()
    request = factory.get(
        f'/loja/{loja.slug}/api/crm-vendas/vendedores/',  # URL com slug
        HTTP_X_LOJA_ID=str(loja.id),
        HTTP_X_TENANT_SLUG=loja.slug,
    )
    
    # Autenticar como owner
    force_authenticate(request, user=loja.owner)
    
    # Aplicar middleware (seta contexto)
    middleware = TenantMiddleware(lambda r: r)
    middleware(request)
    
    # Verificar contexto
    from tenants.middleware import get_current_loja_id
    print(f"Contexto após middleware: loja_id={get_current_loja_id()}\n")
    
    # Criar viewset e chamar list()
    viewset = VendedorViewSet.as_view({'get': 'list'})
    response = viewset(request)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Data: {response.data}\n")
    
    if response.status_code == 200:
        results = response.data.get('results', response.data)
        print(f"Total de vendedores: {len(results) if isinstance(results, list) else 'N/A'}")
        if isinstance(results, list):
            for v in results:
                print(f"  - ID: {v.get('id')}, Nome: {v.get('nome')}, Email: {v.get('email')}, is_admin: {v.get('is_admin')}")
    else:
        print(f"❌ ERRO: {response.data}")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    testar()
