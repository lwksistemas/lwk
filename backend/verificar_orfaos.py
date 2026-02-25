"""
Script simplificado para verificar dados órfãos
Execute: python manage.py shell < verificar_orfaos.py
"""

from django.contrib.auth import get_user_model
from django.db import connection
from superadmin.models import Loja, LojaFinanceiro
from asaas_integration.models import AsaasCustomer, AsaasSubscription, AsaasPayment
from mercadopago_integration.models import MercadoPagoCustomer, LojaPagamento

User = get_user_model()

print("\n" + "="*80)
print("VERIFICAÇÃO DE DADOS ÓRFÃOS")
print("="*80)

# 1. SCHEMAS
print("\n1. VERIFICANDO SCHEMAS...")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
    """)
    schemas = [row[0] for row in cursor.fetchall()]

print(f"Total de schemas: {len(schemas)}")
schemas_orfaos = []
for schema in schemas:
    try:
        loja = Loja.objects.get(schema_name=schema)
        print(f"✅ {schema} → {loja.nome}")
    except Loja.DoesNotExist:
        schemas_orfaos.append(schema)
        print(f"❌ {schema} → ÓRFÃO")

# 2. USUÁRIOS
print("\n2. VERIFICANDO USUÁRIOS...")
usuarios = User.objects.filter(is_superuser=False, is_staff=False)
print(f"Total de usuários: {usuarios.count()}")
usuarios_orfaos = []
for usuario in usuarios:
    try:
        loja = Loja.objects.get(usuarios=usuario)
        print(f"✅ {usuario.username} → {loja.nome}")
    except Loja.DoesNotExist:
        usuarios_orfaos.append(usuario)
        print(f"❌ {usuario.username} → ÓRFÃO")

# 3. FINANCEIRO
print("\n3. VERIFICANDO FINANCEIRO...")
financeiros = LojaFinanceiro.objects.all()
print(f"Total de financeiros: {financeiros.count()}")
financeiros_orfaos = []
for fin in financeiros:
    try:
        loja = Loja.objects.get(financeiro=fin)
        print(f"✅ Financeiro {fin.id} → {loja.nome}")
    except Loja.DoesNotExist:
        financeiros_orfaos.append(fin)
        print(f"❌ Financeiro {fin.id} → ÓRFÃO")

# 4. ASAAS
print("\n4. VERIFICANDO ASAAS...")
asaas_customers = AsaasCustomer.objects.all()
print(f"Total de Asaas Customers: {asaas_customers.count()}")
asaas_customers_orfaos = []
for customer in asaas_customers:
    try:
        loja = Loja.objects.get(slug=customer.loja_slug)
        print(f"✅ Customer {customer.asaas_id} → {loja.nome}")
    except Loja.DoesNotExist:
        asaas_customers_orfaos.append(customer)
        print(f"❌ Customer {customer.asaas_id} (slug: {customer.loja_slug}) → ÓRFÃO")

asaas_subscriptions = AsaasSubscription.objects.all()
print(f"\nTotal de Asaas Subscriptions: {asaas_subscriptions.count()}")
asaas_subscriptions_orfaos = []
for sub in asaas_subscriptions:
    if sub.customer in asaas_customers_orfaos:
        asaas_subscriptions_orfaos.append(sub)
        print(f"❌ Subscription {sub.asaas_id} → Customer órfão")
    else:
        try:
            loja = Loja.objects.get(slug=sub.customer.loja_slug)
            print(f"✅ Subscription {sub.asaas_id} → {loja.nome}")
        except Loja.DoesNotExist:
            asaas_subscriptions_orfaos.append(sub)
            print(f"❌ Subscription {sub.asaas_id} → ÓRFÃO")

asaas_payments = AsaasPayment.objects.all()
print(f"\nTotal de Asaas Payments: {asaas_payments.count()}")
asaas_payments_orfaos = []
for payment in asaas_payments:
    if payment.customer in asaas_customers_orfaos:
        asaas_payments_orfaos.append(payment)
        print(f"❌ Payment {payment.asaas_id} → Customer órfão")
    else:
        try:
            loja = Loja.objects.get(slug=payment.customer.loja_slug)
            print(f"✅ Payment {payment.asaas_id} → {loja.nome}")
        except Loja.DoesNotExist:
            asaas_payments_orfaos.append(payment)
            print(f"❌ Payment {payment.asaas_id} → ÓRFÃO")

# 5. MERCADO PAGO
print("\n5. VERIFICANDO MERCADO PAGO...")
mp_customers = MercadoPagoCustomer.objects.all()
print(f"Total de MP Customers: {mp_customers.count()}")
mp_customers_orfaos = []
for customer in mp_customers:
    try:
        loja = Loja.objects.get(slug=customer.loja_slug)
        print(f"✅ Customer {customer.mercadopago_id} → {loja.nome}")
    except Loja.DoesNotExist:
        mp_customers_orfaos.append(customer)
        print(f"❌ Customer {customer.mercadopago_id} (slug: {customer.loja_slug}) → ÓRFÃO")

mp_pagamentos = LojaPagamento.objects.all()
print(f"\nTotal de MP Pagamentos: {mp_pagamentos.count()}")
mp_pagamentos_orfaos = []
for pag in mp_pagamentos:
    try:
        loja = Loja.objects.get(slug=pag.loja_slug)
        print(f"✅ Pagamento {pag.mercadopago_payment_id} → {loja.nome}")
    except Loja.DoesNotExist:
        mp_pagamentos_orfaos.append(pag)
        print(f"❌ Pagamento {pag.mercadopago_payment_id} (slug: {pag.loja_slug}) → ÓRFÃO")

# 6. LOJAS ATIVAS
print("\n6. LOJAS ATIVAS NO SISTEMA:")
lojas = Loja.objects.all().order_by('nome')
print(f"Total: {lojas.count()}")
for loja in lojas:
    print(f"  🏪 {loja.nome} (slug: {loja.slug}, schema: {loja.schema_name})")

# RESUMO
print("\n" + "="*80)
print("RESUMO")
print("="*80)
print(f"Schemas órfãos: {len(schemas_orfaos)}")
print(f"Usuários órfãos: {len(usuarios_orfaos)}")
print(f"Financeiro órfão: {len(financeiros_orfaos)}")
print(f"Asaas Customers órfãos: {len(asaas_customers_orfaos)}")
print(f"Asaas Subscriptions órfãos: {len(asaas_subscriptions_orfaos)}")
print(f"Asaas Payments órfãos: {len(asaas_payments_orfaos)}")
print(f"MP Customers órfãos: {len(mp_customers_orfaos)}")
print(f"MP Pagamentos órfãos: {len(mp_pagamentos_orfaos)}")

total_orfaos = (
    len(schemas_orfaos) + len(usuarios_orfaos) + len(financeiros_orfaos) +
    len(asaas_customers_orfaos) + len(asaas_subscriptions_orfaos) + len(asaas_payments_orfaos) +
    len(mp_customers_orfaos) + len(mp_pagamentos_orfaos)
)

print(f"\nTOTAL DE ÓRFÃOS: {total_orfaos}")

if total_orfaos > 0:
    print("\n⚠️  SCRIPT DE LIMPEZA:")
    print("="*80)
    
    if schemas_orfaos:
        print("\n# Schemas:")
        for schema in schemas_orfaos:
            print(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
    
    if usuarios_orfaos:
        print("\n# Usuários:")
        ids = [u.id for u in usuarios_orfaos]
        print(f"User.objects.filter(id__in={ids}).delete()")
    
    if financeiros_orfaos:
        print("\n# Financeiro:")
        ids = [f.id for f in financeiros_orfaos]
        print(f"LojaFinanceiro.objects.filter(id__in={ids}).delete()")
    
    if asaas_payments_orfaos:
        print("\n# Asaas Payments:")
        ids = [p.id for p in asaas_payments_orfaos]
        print(f"AsaasPayment.objects.filter(id__in={ids}).delete()")
    
    if asaas_subscriptions_orfaos:
        print("\n# Asaas Subscriptions:")
        ids = [s.id for s in asaas_subscriptions_orfaos]
        print(f"AsaasSubscription.objects.filter(id__in={ids}).delete()")
    
    if asaas_customers_orfaos:
        print("\n# Asaas Customers:")
        ids = [c.id for c in asaas_customers_orfaos]
        print(f"AsaasCustomer.objects.filter(id__in={ids}).delete()")
    
    if mp_pagamentos_orfaos:
        print("\n# MP Pagamentos:")
        ids = [p.id for p in mp_pagamentos_orfaos]
        print(f"LojaPagamento.objects.filter(id__in={ids}).delete()")
    
    if mp_customers_orfaos:
        print("\n# MP Customers:")
        ids = [c.id for c in mp_customers_orfaos]
        print(f"MercadoPagoCustomer.objects.filter(id__in={ids}).delete()")
else:
    print("\n✅ SISTEMA LIMPO! Nenhum dado órfão encontrado.")

print("\n" + "="*80)
