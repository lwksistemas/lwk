#!/usr/bin/env python3
import os, sys, django

sys.path.append('/app' if os.path.exists('/app') else '/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production' if os.path.exists('/app') else 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from django.contrib.auth.models import User

# Verificar dados da loja felix
loja = Loja.objects.get(slug='felix')
financeiro = loja.financeiro
user = User.objects.get(username='felipe')

print('🏪 Loja Felix:')
print(f'   Nome: {loja.nome}')
print(f'   Owner: {loja.owner.username} (ID: {loja.owner.id})')
print(f'   User felipe ID: {user.id}')
print(f'   São o mesmo? {loja.owner.id == user.id}')

print('\n💰 Financeiro:')
print(f'   Status: {financeiro.status_pagamento}')
print(f'   Customer ID: {financeiro.asaas_customer_id}')
print(f'   Payment ID: {financeiro.asaas_payment_id}')
print(f'   Boleto URL: {financeiro.boleto_url[:50] if financeiro.boleto_url else "Não disponível"}')