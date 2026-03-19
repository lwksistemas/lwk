#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from crm_vendas.models import Proposta
from tenants.middleware import set_current_loja_id, set_current_tenant_db
from core.db_config import ensure_loja_database_config

# Configurar contexto
set_current_loja_id(130)
ensure_loja_database_config('loja_22239255889')
set_current_tenant_db('loja_22239255889')

# Verificar propostas
print(f'Total propostas: {Proposta.objects.count()}')
print('\nPropostas:')
for p in Proposta.objects.all().order_by('-id'):
    print(f'  ID={p.id}, titulo={p.titulo}, status_assinatura={p.status_assinatura}')
