#!/usr/bin/env python
"""
Script para sincronizar LojaAssinatura.data_vencimento com FinanceiroLoja.data_proxima_cobranca
para todas as lojas. Corrige o bug onde o cobranca_service sobrescrevia data_vencimento
com a data do boleto pago em vez da próxima cobrança.

Uso:
  heroku run "cd backend && python sincronizar_vencimentos_todas_lojas.py" --app lwksistemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from asaas_integration.models import LojaAssinatura

corrigidos = 0
ok = 0

for assinatura in LojaAssinatura.objects.all():
    try:
        loja = Loja.objects.get(slug=assinatura.loja_slug)
        financeiro = loja.financeiro
        data_correta = financeiro.data_proxima_cobranca

        if not data_correta:
            print(f"⚠️  {loja.nome}: sem data_proxima_cobranca no financeiro")
            continue

        if assinatura.data_vencimento != data_correta:
            print(f"🔧 {loja.nome}:")
            print(f"   LojaAssinatura.data_vencimento: {assinatura.data_vencimento}")
            print(f"   FinanceiroLoja.data_proxima_cobranca: {data_correta}")
            print(f"   Corrigindo → {data_correta}")
            assinatura.data_vencimento = data_correta
            assinatura.save()
            corrigidos += 1
        else:
            print(f"✅ {loja.nome}: OK ({assinatura.data_vencimento})")
            ok += 1

    except Loja.DoesNotExist:
        print(f"⚠️  Loja não encontrada para slug: {assinatura.loja_slug}")
    except Exception as e:
        print(f"❌ {assinatura.loja_nome}: erro - {e}")

print(f"\n📊 Resultado: {corrigidos} corrigidos, {ok} já corretos")
