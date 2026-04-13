#!/usr/bin/env python
"""
Script para sincronizar status dos AsaasPayment locais com o Asaas.
Os pagamentos foram confirmados via webhook mas o AsaasPayment local
ficou com status PENDING porque o webhook não atualizava essa tabela.

Uso:
  heroku run "cd backend && python sincronizar_status_pagamentos.py" --app lwksistemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, AsaasConfig
from asaas_integration.client import AsaasClient

config = AsaasConfig.get_config()
if not config or not config.api_key:
    print("❌ Asaas não configurado")
    exit(1)

client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

# Buscar todos os pagamentos PENDING locais
pendentes = AsaasPayment.objects.filter(status='PENDING')
print(f"📊 {pendentes.count()} pagamentos PENDING no banco local\n")

atualizados = 0
erros = 0

for ap in pendentes:
    try:
        # Consultar status real no Asaas
        data = client._make_request('GET', f'payments/{ap.asaas_id}')
        status_real = data.get('status', '')
        payment_date = data.get('paymentDate')

        if status_real and status_real != ap.status:
            print(f"🔄 {ap.asaas_id}: {ap.status} → {status_real}")
            ap.status = status_real
            if payment_date:
                from datetime import datetime
                from django.utils import timezone
                ap.payment_date = timezone.make_aware(datetime.strptime(payment_date, '%Y-%m-%d'))
            ap.save(update_fields=['status', 'payment_date'])
            atualizados += 1
        else:
            print(f"✅ {ap.asaas_id}: já está correto ({ap.status})")
    except Exception as e:
        print(f"❌ {ap.asaas_id}: erro - {e}")
        erros += 1

print(f"\n📊 Resultado: {atualizados} atualizados, {erros} erros")
