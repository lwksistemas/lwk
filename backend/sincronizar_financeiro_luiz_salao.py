#!/usr/bin/env python
"""
Script para sincronizar FinanceiroLoja com AsaasPayment
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import LojaAssinatura, AsaasPayment
from datetime import date

loja_slug = 'luiz-salao-5889'

try:
    print(f"\n{'='*60}")
    print(f"Sincronizando Financeiro com Asaas - Luiz Salao")
    print(f"{'='*60}\n")
    
    # Buscar loja
    loja = Loja.objects.get(slug=loja_slug)
    financeiro = loja.financeiro
    
    print(f"📊 Dados Atuais do FinanceiroLoja:")
    print(f"   - Data Próxima Cobrança: {financeiro.data_proxima_cobranca}")
    print(f"   - Dia Vencimento: {financeiro.dia_vencimento}")
    print(f"   - Status: {financeiro.status_pagamento}")
    
    # Buscar assinatura Asaas
    loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
    
    print(f"\n📊 Dados da LojaAssinatura:")
    print(f"   - Data Vencimento: {loja_assinatura.data_vencimento}")
    
    # Buscar próximo pagamento pendente no Asaas
    proximo_boleto = AsaasPayment.objects.filter(
        customer=loja_assinatura.asaas_customer,
        status='PENDING',
        due_date__gte=date.today()
    ).order_by('due_date').first()
    
    if proximo_boleto:
        print(f"\n📊 Próximo Boleto Pendente no Asaas:")
        print(f"   - ID: {proximo_boleto.asaas_id}")
        print(f"   - Vencimento: {proximo_boleto.due_date}")
        print(f"   - Status: {proximo_boleto.status}")
        print(f"   - Valor: R$ {proximo_boleto.value}")
        
        # Sincronizar FinanceiroLoja com o próximo boleto
        print(f"\n🔧 Sincronizando FinanceiroLoja...")
        print(f"   - Atualizando data_proxima_cobranca: {financeiro.data_proxima_cobranca} → {proximo_boleto.due_date}")
        
        financeiro.data_proxima_cobranca = proximo_boleto.due_date
        financeiro.save()
        
        # Sincronizar LojaAssinatura também
        if loja_assinatura.data_vencimento != proximo_boleto.due_date:
            print(f"   - Atualizando LojaAssinatura.data_vencimento: {loja_assinatura.data_vencimento} → {proximo_boleto.due_date}")
            loja_assinatura.data_vencimento = proximo_boleto.due_date
            loja_assinatura.save()
        
        print(f"\n✅ Sincronização concluída!")
        
        # Verificar
        financeiro.refresh_from_db()
        loja_assinatura.refresh_from_db()
        
        print(f"\n📊 Dados Após Sincronização:")
        print(f"   - FinanceiroLoja.data_proxima_cobranca: {financeiro.data_proxima_cobranca}")
        print(f"   - LojaAssinatura.data_vencimento: {loja_assinatura.data_vencimento}")
        print(f"   - AsaasPayment.due_date: {proximo_boleto.due_date}")
        
        if financeiro.data_proxima_cobranca == loja_assinatura.data_vencimento == proximo_boleto.due_date:
            print(f"\n✅ TUDO SINCRONIZADO! Todas as datas estão iguais: {proximo_boleto.due_date}")
        else:
            print(f"\n⚠️ ATENÇÃO: Ainda há diferenças nas datas!")
    else:
        print(f"\n❌ Nenhum boleto pendente encontrado no Asaas")
        print(f"   - Buscando todos os pagamentos...")
        
        todos_pagamentos = AsaasPayment.objects.filter(
            customer=loja_assinatura.asaas_customer
        ).order_by('-due_date')
        
        print(f"\n📊 Todos os Pagamentos ({todos_pagamentos.count()}):")
        for pag in todos_pagamentos:
            print(f"   - ID: {pag.asaas_id}, Status: {pag.status}, Vencimento: {pag.due_date}, Valor: R$ {pag.value}")
    
    print(f"\n{'='*60}\n")
    
except Loja.DoesNotExist:
    print(f"❌ Loja {loja_slug} não encontrada")
except LojaAssinatura.DoesNotExist:
    print(f"❌ LojaAssinatura não encontrada para {loja_slug}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
