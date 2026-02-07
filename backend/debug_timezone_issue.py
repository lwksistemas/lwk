#!/usr/bin/env python
"""
Script para debugar problema de timezone
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, LojaAssinatura
from superadmin.models import Loja, FinanceiroLoja
from datetime import date, datetime
from django.utils import timezone

loja_slug = 'luiz-salao-5889'

print(f"\n{'='*60}")
print(f"Debug: Problema de Timezone - Luiz Salao")
print(f"{'='*60}\n")

try:
    loja = Loja.objects.get(slug=loja_slug)
    financeiro = loja.financeiro
    loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
    
    # Buscar próximo boleto
    proximo_boleto = AsaasPayment.objects.filter(
        customer=loja_assinatura.asaas_customer,
        status='PENDING',
        due_date__gte=date.today()
    ).order_by('due_date').first()
    
    print(f"📊 Análise de Datas:")
    print(f"\n1. FinanceiroLoja.data_proxima_cobranca:")
    print(f"   - Valor no banco: {financeiro.data_proxima_cobranca}")
    print(f"   - Tipo: {type(financeiro.data_proxima_cobranca)}")
    print(f"   - Repr: {repr(financeiro.data_proxima_cobranca)}")
    
    print(f"\n2. LojaAssinatura.data_vencimento:")
    print(f"   - Valor no banco: {loja_assinatura.data_vencimento}")
    print(f"   - Tipo: {type(loja_assinatura.data_vencimento)}")
    print(f"   - Repr: {repr(loja_assinatura.data_vencimento)}")
    
    if proximo_boleto:
        print(f"\n3. AsaasPayment.due_date:")
        print(f"   - Valor no banco: {proximo_boleto.due_date}")
        print(f"   - Tipo: {type(proximo_boleto.due_date)}")
        print(f"   - Repr: {repr(proximo_boleto.due_date)}")
        print(f"   - Asaas ID: {proximo_boleto.asaas_id}")
        
        # Verificar se é date ou datetime
        if isinstance(proximo_boleto.due_date, datetime):
            print(f"\n⚠️ PROBLEMA ENCONTRADO!")
            print(f"   - due_date é datetime, deveria ser date")
            print(f"   - Datetime: {proximo_boleto.due_date}")
            print(f"   - Timezone: {proximo_boleto.due_date.tzinfo}")
            print(f"   - Date: {proximo_boleto.due_date.date()}")
            
            # Corrigir
            print(f"\n🔧 Corrigindo...")
            proximo_boleto.due_date = proximo_boleto.due_date.date()
            proximo_boleto.save()
            print(f"✅ Corrigido para: {proximo_boleto.due_date}")
        else:
            print(f"\n✅ due_date é date (correto)")
    
    # Verificar timezone atual
    print(f"\n4. Timezone Info:")
    print(f"   - Timezone atual: {timezone.get_current_timezone()}")
    print(f"   - Data/hora atual: {timezone.now()}")
    print(f"   - Data atual (date): {date.today()}")
    
    # Buscar todos os pagamentos para debug
    todos_pagamentos = AsaasPayment.objects.filter(
        customer=loja_assinatura.asaas_customer
    ).order_by('-due_date')
    
    print(f"\n5. Todos os Pagamentos ({todos_pagamentos.count()}):")
    for pag in todos_pagamentos:
        print(f"   - ID: {pag.asaas_id}")
        print(f"     Status: {pag.status}")
        print(f"     Vencimento: {pag.due_date} (tipo: {type(pag.due_date).__name__})")
        print(f"     Valor: R$ {pag.value}")
        print()
    
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
