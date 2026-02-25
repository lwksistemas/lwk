"""
Script para debugar duplicação de cobranças no Asaas

Uso:
heroku run python manage.py shell < debug_duplicacao_asaas.py --app lwksistemas-38ad47519238

Ou no Django shell:
exec(open('debug_duplicacao_asaas.py').read())
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, LojaAssinatura, AsaasCustomer
from superadmin.models import Loja, FinanceiroLoja
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"\n{'='*80}")
print(f"DEBUG: DUPLICAÇÃO DE COBRANÇAS NO ASAAS")
print(f"{'='*80}\n")

# Listar últimas 5 lojas criadas com Asaas
lojas_asaas = Loja.objects.filter(
    provedor_boleto_preferido='asaas',
    is_active=True
).order_by('-created_at')[:5]

for loja in lojas_asaas:
    print(f"\n{'='*80}")
    print(f"Loja: {loja.nome} ({loja.slug})")
    print(f"Criada em: {loja.created_at}")
    print(f"Provedor: {loja.provedor_boleto_preferido}")
    print(f"{'='*80}")
    
    # Buscar FinanceiroLoja
    try:
        financeiro = loja.financeiro
        print(f"\nFinanceiroLoja:")
        print(f"  ID: {financeiro.id}")
        print(f"  Status: {financeiro.status_pagamento}")
        print(f"  Asaas Customer ID: {financeiro.asaas_customer_id}")
        print(f"  Asaas Payment ID: {financeiro.asaas_payment_id}")
    except Exception as e:
        print(f"  ❌ Erro ao buscar FinanceiroLoja: {e}")
    
    # Buscar LojaAssinatura
    try:
        assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
        print(f"\nLojaAssinatura:")
        print(f"  ID: {assinatura.id}")
        print(f"  Customer: {assinatura.asaas_customer.name if assinatura.asaas_customer else 'N/A'}")
        print(f"  Customer Asaas ID: {assinatura.asaas_customer.asaas_id if assinatura.asaas_customer else 'N/A'}")
        print(f"  Current Payment: {assinatura.current_payment.asaas_id if assinatura.current_payment else 'N/A'}")
    except LojaAssinatura.DoesNotExist:
        print(f"\n  ⚠️ LojaAssinatura não encontrada")
    except Exception as e:
        print(f"\n  ❌ Erro ao buscar LojaAssinatura: {e}")
    
    # Buscar todos os AsaasPayment relacionados
    try:
        # Buscar por external_reference
        payments = AsaasPayment.objects.filter(
            external_reference__icontains=loja.slug
        ).order_by('-created_at')
        
        print(f"\nAsaasPayment (total: {payments.count()}):")
        for i, payment in enumerate(payments, 1):
            print(f"  {i}. Payment ID: {payment.asaas_id}")
            print(f"     Status: {payment.status}")
            print(f"     Valor: R$ {payment.value}")
            print(f"     Vencimento: {payment.due_date}")
            print(f"     Criado em: {payment.created_at}")
            print(f"     External Ref: {payment.external_reference}")
            print()
        
        if payments.count() > 1:
            print(f"  ⚠️ DUPLICAÇÃO DETECTADA: {payments.count()} pagamentos para a mesma loja!")
            
            # Verificar se são pagamentos idênticos
            if payments.count() == 2:
                p1, p2 = payments[0], payments[1]
                print(f"\n  Comparação:")
                print(f"    Valor igual: {p1.value == p2.value}")
                print(f"    Vencimento igual: {p1.due_date == p2.due_date}")
                print(f"    Customer igual: {p1.customer_id == p2.customer_id}")
                print(f"    Diferença de tempo: {abs((p1.created_at - p2.created_at).total_seconds())} segundos")
                
    except Exception as e:
        print(f"  ❌ Erro ao buscar AsaasPayment: {e}")

print(f"\n{'='*80}")
print(f"FIM DO DEBUG")
print(f"{'='*80}\n")

# Sugestões
print("\n📋 ANÁLISE:")
print("Se houver duplicação, as possíveis causas são:")
print("1. Signal sendo chamado 2 vezes (bug no Django)")
print("2. Código criando cobrança em 2 lugares diferentes")
print("3. Retry automático criando cobrança duplicada")
print("4. Webhook criando cobrança adicional")
print("\n💡 PRÓXIMOS PASSOS:")
print("1. Verificar logs do Heroku no momento da criação da loja")
print("2. Adicionar logs detalhados no signal create_asaas_subscription_on_financeiro_creation")
print("3. Verificar se há código antigo criando cobrança fora do CobrancaService")
