#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from crm_vendas.models import Proposta, VendedorUsuario

loja = Loja.objects.get(slug='41449198000172')
print(f'Loja: {loja.nome}')
print(f'Owner: {loja.owner.username} (ID: {loja.owner.id})')
print()

# Verificar vendedores
vendedores = VendedorUsuario.objects.filter(loja=loja)
print(f'Vendedores cadastrados: {vendedores.count()}')
for v in vendedores:
    print(f'  - {v.user.username} (ID: {v.id}, Admin: {v.is_admin}, Ativo: {v.is_active})')
print()

# Verificar propostas
propostas = Proposta.objects.filter(loja=loja)
print(f'Propostas cadastradas: {propostas.count()}')
for p in propostas[:10]:
    vendedor_nome = p.vendedor.user.username if p.vendedor else "Sem vendedor"
    cliente_nome = p.cliente.nome if p.cliente else "Sem cliente"
    print(f'  - Proposta #{p.numero} - Cliente: {cliente_nome} - Vendedor: {vendedor_nome}')
