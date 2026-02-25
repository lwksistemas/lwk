"""
Script para verificar dados órfãos após exclusão de lojas de teste
Verifica: schemas, usuários, financeiro, assinaturas, pagamentos, etc.
"""

import os
import sys
import django

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from superadmin.models import Loja, LojaFinanceiro
from asaas_integration.models import AsaasCustomer, AsaasSubscription, AsaasPayment
from mercadopago_integration.models import MercadoPagoCustomer, LojaPagamento

User = get_user_model()

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def verificar_schemas_orfaos():
    """Verifica schemas no PostgreSQL sem loja correspondente"""
    print_section("VERIFICANDO SCHEMAS ÓRFÃOS")
    
    with connection.cursor() as cursor:
        # Listar todos os schemas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name;
        """)
        schemas = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📊 Total de schemas encontrados: {len(schemas)}")
    
    # Verificar quais schemas não têm loja correspondente
    schemas_orfaos = []
    for schema in schemas:
        try:
            loja = Loja.objects.get(schema_name=schema)
            print(f"✅ {schema} → Loja: {loja.nome} (ID: {loja.id})")
        except Loja.DoesNotExist:
            schemas_orfaos.append(schema)
            print(f"❌ {schema} → SEM LOJA (ÓRFÃO)")
    
    if schemas_orfaos:
        print(f"\n⚠️  ENCONTRADOS {len(schemas_orfaos)} SCHEMAS ÓRFÃOS:")
        for schema in schemas_orfaos:
            print(f"   - {schema}")
        
        print("\n💡 Para remover schemas órfãos, execute:")
        for schema in schemas_orfaos:
            print(f'   DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
    else:
        print("\n✅ Nenhum schema órfão encontrado!")
    
    return schemas_orfaos

def verificar_usuarios_orfaos():
    """Verifica usuários sem loja correspondente"""
    print_section("VERIFICANDO USUÁRIOS ÓRFÃOS")
    
    usuarios = User.objects.filter(is_superuser=False, is_staff=False)
    print(f"\n📊 Total de usuários (não admin): {usuarios.count()}")
    
    usuarios_orfaos = []
    for usuario in usuarios:
        try:
            loja = Loja.objects.get(usuarios=usuario)
            print(f"✅ {usuario.username} ({usuario.email}) → Loja: {loja.nome}")
        except Loja.DoesNotExist:
            usuarios_orfaos.append(usuario)
            print(f"❌ {usuario.username} ({usuario.email}) → SEM LOJA (ÓRFÃO)")
    
    if usuarios_orfaos:
        print(f"\n⚠️  ENCONTRADOS {len(usuarios_orfaos)} USUÁRIOS ÓRFÃOS:")
        for usuario in usuarios_orfaos:
            print(f"   - ID: {usuario.id}, Username: {usuario.username}, Email: {usuario.email}")
        
        print("\n💡 Para remover usuários órfãos:")
        print("   User.objects.filter(id__in=[...]).delete()")
    else:
        print("\n✅ Nenhum usuário órfão encontrado!")
    
    return usuarios_orfaos

def verificar_financeiro_orfao():
    """Verifica registros de financeiro sem loja"""
    print_section("VERIFICANDO FINANCEIRO ÓRFÃO")
    
    financeiros = LojaFinanceiro.objects.all()
    print(f"\n📊 Total de registros financeiros: {financeiros.count()}")
    
    financeiros_orfaos = []
    for financeiro in financeiros:
        try:
            loja = Loja.objects.get(financeiro=financeiro)
            print(f"✅ Financeiro ID {financeiro.id} → Loja: {loja.nome}")
        except Loja.DoesNotExist:
            financeiros_orfaos.append(financeiro)
            print(f"❌ Financeiro ID {financeiro.id} → SEM LOJA (ÓRFÃO)")
    
    if financeiros_orfaos:
        print(f"\n⚠️  ENCONTRADOS {len(financeiros_orfaos)} REGISTROS FINANCEIROS ÓRFÃOS:")
        for fin in financeiros_orfaos:
            print(f"   - ID: {fin.id}, Status: {fin.status_pagamento}, Gateway: {fin.gateway_pagamento}")
    else:
        print("\n✅ Nenhum registro financeiro órfão encontrado!")
    
    return financeiros_orfaos

def verificar_asaas_orfaos():
    """Verifica dados do Asaas sem loja correspondente"""
    print_section("VERIFICANDO DADOS ASAAS ÓRFÃOS")
    
    # Customers
    customers = AsaasCustomer.objects.all()
    print(f"\n📊 Total de Asaas Customers: {customers.count()}")
    
    customers_orfaos = []
    for customer in customers:
        try:
            loja = Loja.objects.get(slug=customer.loja_slug)
            print(f"✅ Customer {customer.asaas_id} → Loja: {loja.nome}")
        except Loja.DoesNotExist:
            customers_orfaos.append(customer)
            print(f"❌ Customer {customer.asaas_id} (slug: {customer.loja_slug}) → SEM LOJA (ÓRFÃO)")
    
    # Subscriptions
    subscriptions = AsaasSubscription.objects.all()
    print(f"\n📊 Total de Asaas Subscriptions: {subscriptions.count()}")
    
    subscriptions_orfaos = []
    for subscription in subscriptions:
        if subscription.customer not in customers_orfaos:
            try:
                loja = Loja.objects.get(slug=subscription.customer.loja_slug)
                print(f"✅ Subscription {subscription.asaas_id} → Loja: {loja.nome}")
            except Loja.DoesNotExist:
                subscriptions_orfaos.append(subscription)
                print(f"❌ Subscription {subscription.asaas_id} → SEM LOJA (ÓRFÃO)")
        else:
            subscriptions_orfaos.append(subscription)
            print(f"❌ Subscription {subscription.asaas_id} → Customer órfão")
    
    # Payments
    payments = AsaasPayment.objects.all()
    print(f"\n📊 Total de Asaas Payments: {payments.count()}")
    
    payments_orfaos = []
    for payment in payments:
        if payment.customer not in customers_orfaos:
            try:
                loja = Loja.objects.get(slug=payment.customer.loja_slug)
                print(f"✅ Payment {payment.asaas_id} → Loja: {loja.nome}")
            except Loja.DoesNotExist:
                payments_orfaos.append(payment)
                print(f"❌ Payment {payment.asaas_id} → SEM LOJA (ÓRFÃO)")
        else:
            payments_orfaos.append(payment)
            print(f"❌ Payment {payment.asaas_id} → Customer órfão")
    
    total_orfaos = len(customers_orfaos) + len(subscriptions_orfaos) + len(payments_orfaos)
    
    if total_orfaos > 0:
        print(f"\n⚠️  ENCONTRADOS {total_orfaos} REGISTROS ASAAS ÓRFÃOS:")
        print(f"   - Customers: {len(customers_orfaos)}")
        print(f"   - Subscriptions: {len(subscriptions_orfaos)}")
        print(f"   - Payments: {len(payments_orfaos)}")
    else:
        print("\n✅ Nenhum registro Asaas órfão encontrado!")
    
    return {
        'customers': customers_orfaos,
        'subscriptions': subscriptions_orfaos,
        'payments': payments_orfaos
    }

def verificar_mercadopago_orfaos():
    """Verifica dados do Mercado Pago sem loja correspondente"""
    print_section("VERIFICANDO DADOS MERCADO PAGO ÓRFÃOS")
    
    # Customers
    customers = MercadoPagoCustomer.objects.all()
    print(f"\n📊 Total de MercadoPago Customers: {customers.count()}")
    
    customers_orfaos = []
    for customer in customers:
        try:
            loja = Loja.objects.get(slug=customer.loja_slug)
            print(f"✅ Customer {customer.mercadopago_id} → Loja: {loja.nome}")
        except Loja.DoesNotExist:
            customers_orfaos.append(customer)
            print(f"❌ Customer {customer.mercadopago_id} (slug: {customer.loja_slug}) → SEM LOJA (ÓRFÃO)")
    
    # Pagamentos
    pagamentos = LojaPagamento.objects.all()
    print(f"\n📊 Total de LojaPagamentos: {pagamentos.count()}")
    
    pagamentos_orfaos = []
    for pagamento in pagamentos:
        try:
            loja = Loja.objects.get(slug=pagamento.loja_slug)
            print(f"✅ Pagamento {pagamento.mercadopago_payment_id} → Loja: {loja.nome}")
        except Loja.DoesNotExist:
            pagamentos_orfaos.append(pagamento)
            print(f"❌ Pagamento {pagamento.mercadopago_payment_id} (slug: {pagamento.loja_slug}) → SEM LOJA (ÓRFÃO)")
    
    total_orfaos = len(customers_orfaos) + len(pagamentos_orfaos)
    
    if total_orfaos > 0:
        print(f"\n⚠️  ENCONTRADOS {total_orfaos} REGISTROS MERCADO PAGO ÓRFÃOS:")
        print(f"   - Customers: {len(customers_orfaos)}")
        print(f"   - Pagamentos: {len(pagamentos_orfaos)}")
    else:
        print("\n✅ Nenhum registro Mercado Pago órfão encontrado!")
    
    return {
        'customers': customers_orfaos,
        'pagamentos': pagamentos_orfaos
    }

def verificar_lojas_ativas():
    """Lista todas as lojas ativas no sistema"""
    print_section("LOJAS ATIVAS NO SISTEMA")
    
    lojas = Loja.objects.all().order_by('nome')
    print(f"\n📊 Total de lojas: {lojas.count()}")
    
    for loja in lojas:
        print(f"\n🏪 {loja.nome}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Schema: {loja.schema_name}")
        print(f"   - Usuários: {loja.usuarios.count()}")
        print(f"   - Gateway: {loja.financeiro.gateway_pagamento if hasattr(loja, 'financeiro') else 'N/A'}")
        print(f"   - Status: {loja.financeiro.status_pagamento if hasattr(loja, 'financeiro') else 'N/A'}")

def gerar_script_limpeza(schemas_orfaos, usuarios_orfaos, financeiros_orfaos, asaas_orfaos, mp_orfaos):
    """Gera script SQL/Python para limpar dados órfãos"""
    print_section("SCRIPT DE LIMPEZA")
    
    tem_orfaos = (
        schemas_orfaos or 
        usuarios_orfaos or 
        financeiros_orfaos or 
        any(asaas_orfaos.values()) or 
        any(mp_orfaos.values())
    )
    
    if not tem_orfaos:
        print("\n✅ Nenhum dado órfão encontrado! Sistema limpo.")
        return
    
    print("\n⚠️  ATENÇÃO: Execute os comandos abaixo com cuidado!")
    print("\n# ============ SCRIPT DE LIMPEZA ============\n")
    
    # Schemas
    if schemas_orfaos:
        print("# --- Remover Schemas Órfãos ---")
        print("# Execute no PostgreSQL:")
        for schema in schemas_orfaos:
            print(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
        print()
    
    # Usuários
    if usuarios_orfaos:
        print("# --- Remover Usuários Órfãos ---")
        print("# Execute no Django shell:")
        ids = [u.id for u in usuarios_orfaos]
        print(f"User.objects.filter(id__in={ids}).delete()")
        print()
    
    # Financeiro
    if financeiros_orfaos:
        print("# --- Remover Financeiro Órfão ---")
        print("# Execute no Django shell:")
        ids = [f.id for f in financeiros_orfaos]
        print(f"LojaFinanceiro.objects.filter(id__in={ids}).delete()")
        print()
    
    # Asaas
    if any(asaas_orfaos.values()):
        print("# --- Remover Dados Asaas Órfãos ---")
        print("# Execute no Django shell:")
        if asaas_orfaos['payments']:
            ids = [p.id for p in asaas_orfaos['payments']]
            print(f"AsaasPayment.objects.filter(id__in={ids}).delete()")
        if asaas_orfaos['subscriptions']:
            ids = [s.id for s in asaas_orfaos['subscriptions']]
            print(f"AsaasSubscription.objects.filter(id__in={ids}).delete()")
        if asaas_orfaos['customers']:
            ids = [c.id for c in asaas_orfaos['customers']]
            print(f"AsaasCustomer.objects.filter(id__in={ids}).delete()")
        print()
    
    # Mercado Pago
    if any(mp_orfaos.values()):
        print("# --- Remover Dados Mercado Pago Órfãos ---")
        print("# Execute no Django shell:")
        if mp_orfaos['pagamentos']:
            ids = [p.id for p in mp_orfaos['pagamentos']]
            print(f"LojaPagamento.objects.filter(id__in={ids}).delete()")
        if mp_orfaos['customers']:
            ids = [c.id for c in mp_orfaos['customers']]
            print(f"MercadoPagoCustomer.objects.filter(id__in={ids}).delete()")
        print()

def main():
    print("\n" + "=" * 80)
    print("  VERIFICAÇÃO DE DADOS ÓRFÃOS PÓS-EXCLUSÃO DE LOJAS")
    print("=" * 80)
    
    # Executar verificações
    schemas_orfaos = verificar_schemas_orfaos()
    usuarios_orfaos = verificar_usuarios_orfaos()
    financeiros_orfaos = verificar_financeiro_orfao()
    asaas_orfaos = verificar_asaas_orfaos()
    mp_orfaos = verificar_mercadopago_orfaos()
    
    # Listar lojas ativas
    verificar_lojas_ativas()
    
    # Gerar script de limpeza
    gerar_script_limpeza(
        schemas_orfaos,
        usuarios_orfaos,
        financeiros_orfaos,
        asaas_orfaos,
        mp_orfaos
    )
    
    # Resumo final
    print_section("RESUMO FINAL")
    print(f"\n📊 Schemas órfãos: {len(schemas_orfaos)}")
    print(f"📊 Usuários órfãos: {len(usuarios_orfaos)}")
    print(f"📊 Financeiro órfão: {len(financeiros_orfaos)}")
    print(f"📊 Asaas órfãos: {sum(len(v) for v in asaas_orfaos.values())}")
    print(f"📊 Mercado Pago órfãos: {sum(len(v) for v in mp_orfaos.values())}")
    
    total_orfaos = (
        len(schemas_orfaos) +
        len(usuarios_orfaos) +
        len(financeiros_orfaos) +
        sum(len(v) for v in asaas_orfaos.values()) +
        sum(len(v) for v in mp_orfaos.values())
    )
    
    if total_orfaos > 0:
        print(f"\n⚠️  TOTAL DE DADOS ÓRFÃOS: {total_orfaos}")
        print("\n💡 Execute o script de limpeza acima para remover os dados órfãos.")
    else:
        print("\n✅ SISTEMA LIMPO! Nenhum dado órfão encontrado.")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
