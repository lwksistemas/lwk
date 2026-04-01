#!/bin/bash
# Script para emitir nota fiscal manualmente para pagamento já confirmado

echo "📄 Emitindo nota fiscal para HARMONIS..."
echo "========================================"
echo ""

heroku run "python backend/manage.py shell -c \"
from asaas_integration.invoice_service import emitir_nf_para_pagamento, get_invoice_client
from superadmin.models import Loja

# Buscar loja HARMONIS
loja = Loja.objects.filter(nome__icontains='HARMONIS').first()
if not loja:
    print('❌ Loja HARMONIS não encontrada')
    exit(1)

print(f'✅ Loja encontrada: {loja.nome}')

# ID do pagamento confirmado (do log)
payment_id = 'pay_hl9cjbdnb27x5872'
value = 5.00
description = 'Assinatura Profissional Clínica (Mensal) - Loja HARMONIS'

print(f'📋 Payment ID: {payment_id}')
print(f'💰 Valor: R$ {value}')
print()

# Emitir nota fiscal
print('📄 Emitindo nota fiscal...')
result = emitir_nf_para_pagamento(
    asaas_payment_id=payment_id,
    loja=loja,
    value=value,
    description=description,
    send_email=True
)

print()
if result['success']:
    print(f'✅ Nota fiscal emitida com sucesso!')
    print(f'   Invoice ID: {result[\\\"invoice_id\\\"]}')
    if result['email_sent']:
        print(f'   ✅ Email enviado')
else:
    print(f'❌ Erro ao emitir nota fiscal:')
    print(f'   {result[\\\"error\\\"]}')
\"" -a lwksistemas
