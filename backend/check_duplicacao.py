#!/usr/bin/env python
"""
Script simplificado para verificar duplicação de cobranças no Asaas
Executar: heroku run python backend/check_duplicacao.py --app lwksistemas
"""
import os
import sys
import django

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, LojaAssinatura
from superadmin.models import Loja

print(f"\n{'='*80}")
print(f"DEBUG: DUPLICAÇÃO DE COBRANÇAS NO ASAAS")
print(f"{'='*80}\n")

# Listar últimas 10 lojas criadas com Asaas
lojas_asaas = Loja.objects.filter(
    provedor_boleto_preferido='asaas',
    is_active=True
).order_by('-created_at')[:10]

print(f"Total de lojas com Asaas: {lojas_asaas.count()}\n")

duplicacoes_encontradas = 0

for loja in lojas_asaas:
    # Buscar todos os AsaasPayment relacionados
    payments = AsaasPayment.objects.filter(
        external_reference__icontains=loja.slug
    ).order_by('-created_at')
    
    if payments.count() > 1:
        duplicacoes_encontradas += 1
        print(f"\n{'='*80}")
        print(f"⚠️ DUPLICAÇÃO DETECTADA!")
        print(f"{'='*80}")
        print(f"Loja: {loja.nome} ({loja.slug})")
        print(f"Criada em: {loja.created_at}")
        print(f"Total de pagamentos: {payments.count()}")
        
        for i, payment in enumerate(payments, 1):
            print(f"\n  Pagamento {i}:")
            print(f"    Payment ID: {payment.asaas_id}")
            print(f"    Status: {payment.status}")
            print(f"    Valor: R$ {payment.value}")
            print(f"    Vencimento: {payment.due_date}")
            print(f"    Criado em: {payment.created_at}")
        
        # Comparar se são idênticos
        if payments.count() == 2:
            p1, p2 = payments[0], payments[1]
            diff_segundos = abs((p1.created_at - p2.created_at).total_seconds())
            print(f"\n  Análise:")
            print(f"    Valor igual: {p1.value == p2.value}")
            print(f"    Vencimento igual: {p1.due_date == p2.due_date}")
            print(f"    Customer igual: {p1.customer_id == p2.customer_id}")
            print(f"    Diferença de tempo: {diff_segundos:.2f} segundos")
            
            if diff_segundos < 5:
                print(f"    ⚠️ Criados quase simultaneamente (< 5s) - provável bug no signal")
            elif diff_segundos < 60:
                print(f"    ⚠️ Criados em menos de 1 minuto - possível retry")
            else:
                print(f"    ℹ️ Criados com diferença significativa - pode ser renovação")

print(f"\n{'='*80}")
print(f"RESUMO")
print(f"{'='*80}")
print(f"Total de lojas verificadas: {lojas_asaas.count()}")
print(f"Lojas com duplicação: {duplicacoes_encontradas}")

if duplicacoes_encontradas > 0:
    print(f"\n⚠️ AÇÃO NECESSÁRIA:")
    print(f"   {duplicacoes_encontradas} loja(s) com cobranças duplicadas")
    print(f"   Verificar logs do Heroku para identificar causa")
    print(f"   Considerar cancelar cobranças duplicadas no painel do Asaas")
else:
    print(f"\n✅ Nenhuma duplicação encontrada!")
    print(f"   A correção v721 está funcionando corretamente")

print(f"\n{'='*80}\n")
