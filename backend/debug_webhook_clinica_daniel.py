#!/usr/bin/env python
"""
Script para debugar webhook do Mercado Pago - Clinica Daniel
Executar: heroku run python backend/debug_webhook_clinica_daniel.py --app lwksistemas
"""
import os
import sys
import django

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja, EmailRetry
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

print(f"\n{'='*80}")
print(f"DEBUG: Webhook Mercado Pago - Clinica Daniel")
print(f"Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"{'='*80}\n")

try:
    loja = Loja.objects.get(slug='clinica-daniel-5889')
    financeiro = loja.financeiro
    
    print(f"📋 STATUS ATUAL")
    print(f"   Loja: {loja.nome}")
    print(f"   Status pagamento: {financeiro.status_pagamento}")
    print(f"   Senha enviada: {financeiro.senha_enviada}")
    print(f"   Total pagamentos: {financeiro.total_pagamentos}")
    
    if financeiro.data_ultimo_pagamento:
        print(f"   Último pagamento: {financeiro.data_ultimo_pagamento.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        print(f"   Último pagamento: Nenhum")
    
    if financeiro.data_envio_senha:
        print(f"   Data envio senha: {financeiro.data_envio_senha.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        print(f"   Data envio senha: Não enviada")
    
    print(f"\n🔑 PAYMENT IDs")
    print(f"   Boleto: {financeiro.mercadopago_payment_id or 'N/A'}")
    print(f"   PIX: {financeiro.mercadopago_pix_payment_id or 'N/A'}")
    
    # Verificar tentativas de email
    print(f"\n📧 TENTATIVAS DE EMAIL")
    email_retries = EmailRetry.objects.filter(
        loja=loja
    ).order_by('-created_at')
    
    if email_retries.exists():
        print(f"   Total de tentativas: {email_retries.count()}")
        for retry in email_retries[:5]:
            status_emoji = "✅" if retry.status == 'sent' else "❌" if retry.status == 'failed' else "⏳"
            print(f"   {status_emoji} {retry.created_at.strftime('%d/%m/%Y %H:%M:%S')} - {retry.status}")
            if retry.error_message:
                print(f"      Erro: {retry.error_message[:100]}")
    else:
        print(f"   ⚠️ Nenhuma tentativa de email registrada")
        print(f"   Isso indica que o signal on_payment_confirmed NÃO foi disparado")
    
    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO")
    print(f"{'='*80}\n")
    
    if financeiro.status_pagamento == 'ativo' and financeiro.senha_enviada:
        print(f"✅ Sistema funcionando corretamente")
        print(f"   Pagamento processado e senha enviada")
    elif financeiro.status_pagamento == 'ativo' and not financeiro.senha_enviada:
        print(f"⚠️ PROBLEMA: Pagamento processado mas senha não enviada")
        print(f"   Possíveis causas:")
        print(f"   1. Webhook não foi recebido pelo sistema")
        print(f"   2. Signal on_payment_confirmed não disparou")
        print(f"   3. Erro no envio do email")
        print(f"\n   SOLUÇÃO:")
        print(f"   Executar: heroku run python backend/fix_financeiro_mercadopago.py --app lwksistemas")
    else:
        print(f"⚠️ PROBLEMA: Webhook não processou o pagamento")
        print(f"   Status atual: {financeiro.status_pagamento}")
        print(f"   Mercado Pago mostra: APROVADO")
        print(f"   Sistema mostra: {financeiro.status_pagamento.upper()}")
        print(f"\n   Possíveis causas:")
        print(f"   1. Webhook não foi enviado pelo Mercado Pago")
        print(f"   2. Webhook foi enviado mas não processado")
        print(f"   3. Payment ID não corresponde ao registrado")
        print(f"\n   SOLUÇÃO:")
        print(f"   Executar: heroku run python backend/fix_financeiro_mercadopago.py --app lwksistemas")
    
    print(f"\n{'='*80}\n")
    
except Loja.DoesNotExist:
    print(f"❌ ERRO: Loja 'clinica-daniel-5889' não encontrada")
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
