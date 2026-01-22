#!/usr/bin/env python3
import os, sys, django

sys.path.append('/app' if os.path.exists('/app') else '/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production' if os.path.exists('/app') else 'config.settings')
django.setup()

from asaas_integration.models import AsaasCustomer, AsaasPayment
from superadmin.models import Loja

# Verificar se o cliente existe
customer_id = 'cus_000007469087'
payment_id = 'pay_cgi67bfre2gdiuby'

print(f'🔍 Verificando webhook com erro:')
print(f'   Customer ID: {customer_id}')
print(f'   Payment ID: {payment_id}')

# Buscar cliente
try:
    customer = AsaasCustomer.objects.get(asaas_id=customer_id)
    print(f'✅ Cliente encontrado: {customer.name}')
    print(f'   Email: {customer.email}')
    print(f'   CPF/CNPJ: {customer.cpf_cnpj}')
except AsaasCustomer.DoesNotExist:
    print(f'❌ Cliente {customer_id} NÃO encontrado!')

# Buscar pagamento
try:
    payment = AsaasPayment.objects.get(asaas_id=payment_id)
    print(f'✅ Pagamento encontrado: {payment.description}')
except AsaasPayment.DoesNotExist:
    print(f'❌ Pagamento {payment_id} NÃO encontrado!')

# Verificar loja pelo external_reference
external_ref = 'loja_loja-final-teste_assinatura'
loja_slug = external_ref.replace('loja_', '').replace('_assinatura', '')
print(f'\n🏪 Verificando loja pelo external_reference:')
print(f'   External Reference: {external_ref}')
print(f'   Loja Slug extraído: {loja_slug}')

try:
    loja = Loja.objects.get(slug=loja_slug, is_active=True)
    print(f'✅ Loja encontrada: {loja.nome}')
    print(f'   Owner: {loja.owner.username}')
except Loja.DoesNotExist:
    print(f'❌ Loja {loja_slug} NÃO encontrada!')

# Listar todas as lojas para debug
print(f'\n📋 Todas as lojas ativas:')
for loja in Loja.objects.filter(is_active=True):
    print(f'   • {loja.slug} - {loja.nome}')

# Listar todos os clientes Asaas
print(f'\n👥 Todos os clientes Asaas:')
for customer in AsaasCustomer.objects.all():
    print(f'   • {customer.asaas_id} - {customer.name} ({customer.email})')