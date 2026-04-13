#!/usr/bin/env python
"""
Script para corrigir data_vencimento da LojaAssinatura da FELIX REPRESENTACOES.

Problema: A loja pagou plano anual, mas o data_vencimento na LojaAssinatura
ficou com a data do boleto pago (14/04/2026) em vez da próxima cobrança (14/04/2027).

Causa: O update_or_create no cobranca_service.py sobrescrevia data_vencimento
com payment.due_date toda vez que uma cobrança era criada.

Uso:
  heroku run "cd backend && python corrigir_vencimento_felix.py" --app lwksistemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import LojaAssinatura

LOJA_SLUG = '41449198000172'

try:
    loja = Loja.objects.get(slug=LOJA_SLUG)
    print(f"✅ Loja encontrada: {loja.nome}")
    print(f"   Slug: {loja.slug}")
    print(f"   Tipo assinatura: {loja.get_tipo_assinatura_display()}")

    financeiro = loja.financeiro
    print(f"\n📊 FinanceiroLoja:")
    print(f"   Status: {financeiro.status_pagamento}")
    print(f"   Data próxima cobrança: {financeiro.data_proxima_cobranca}")
    print(f"   Último pagamento: {financeiro.ultimo_pagamento}")

    try:
        loja_assinatura = LojaAssinatura.objects.get(loja_slug=LOJA_SLUG)
        print(f"\n📋 LojaAssinatura:")
        print(f"   data_vencimento atual: {loja_assinatura.data_vencimento}")
        print(f"   current_payment: {loja_assinatura.current_payment}")
        if loja_assinatura.current_payment:
            print(f"   current_payment.due_date: {loja_assinatura.current_payment.due_date}")
            print(f"   current_payment.status: {loja_assinatura.current_payment.status}")

        # A data correta é a data_proxima_cobranca do FinanceiroLoja
        data_correta = financeiro.data_proxima_cobranca

        if data_correta and loja_assinatura.data_vencimento != data_correta:
            print(f"\n🔧 Corrigindo data_vencimento:")
            print(f"   De: {loja_assinatura.data_vencimento}")
            print(f"   Para: {data_correta}")

            loja_assinatura.data_vencimento = data_correta
            loja_assinatura.save()
            print(f"✅ LojaAssinatura.data_vencimento corrigida para {data_correta}")
        else:
            print(f"\n✅ data_vencimento já está correto: {loja_assinatura.data_vencimento}")

    except LojaAssinatura.DoesNotExist:
        print(f"\n❌ LojaAssinatura não encontrada para slug: {LOJA_SLUG}")

except Loja.DoesNotExist:
    print(f"❌ Loja não encontrada: {LOJA_SLUG}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
