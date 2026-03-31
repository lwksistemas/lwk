#!/usr/bin/env python
"""
Script para atualizar financeiro após pagamento do Mercado Pago
Executar: heroku run python backend/fix_financeiro_mercadopago.py --app lwksistemas
"""
import os
import sys
import django

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from django.utils import timezone
from datetime import date
from calendar import monthrange

print(f"\n{'='*80}")
print(f"ATUALIZAÇÃO DE FINANCEIRO - MERCADO PAGO")
print(f"{'='*80}\n")

# Buscar lojas com Mercado Pago e pagamento pendente
lojas_pendentes = Loja.objects.filter(
    provedor_boleto_preferido='mercadopago',
    is_active=True
).select_related('financeiro')

print(f"Total de lojas com Mercado Pago: {lojas_pendentes.count()}\n")

for loja in lojas_pendentes:
    try:
        financeiro = loja.financeiro
        
        # Verificar se tem payment_id do Mercado Pago
        if not financeiro.mercadopago_payment_id and not financeiro.mercadopago_pix_payment_id:
            continue
        
        # Verificar se status é pendente
        if financeiro.status_pagamento == 'ativo':
            continue
        
        print(f"\n{'='*80}")
        print(f"Loja: {loja.nome} ({loja.slug})")
        print(f"{'='*80}")
        print(f"Status atual: {financeiro.status_pagamento}")
        print(f"Boleto ID: {financeiro.mercadopago_payment_id}")
        print(f"PIX ID: {financeiro.mercadopago_pix_payment_id}")
        
        # Verificar status no Mercado Pago
        from superadmin.models import MercadoPagoConfig
        from superadmin.mercadopago_service import MercadoPagoClient
        
        config = MercadoPagoConfig.get_config()
        if not config or not config.access_token:
            print("❌ Mercado Pago não configurado")
            continue
        
        client = MercadoPagoClient(config.access_token)
        
        # Verificar PIX primeiro (mais comum)
        payment_id_to_check = financeiro.mercadopago_pix_payment_id or financeiro.mercadopago_payment_id
        
        print(f"\n🔍 Consultando pagamento {payment_id_to_check} na API do Mercado Pago...")
        payment_data = client.get_payment(str(payment_id_to_check))
        
        if not payment_data:
            print(f"❌ Pagamento não encontrado na API")
            continue
        
        status_mp = payment_data.get('status', '')
        print(f"Status no Mercado Pago: {status_mp}")
        print(f"Valor: R$ {payment_data.get('transaction_amount', 0)}")
        print(f"Data aprovação: {payment_data.get('date_approved', 'N/A')}")
        
        if status_mp == 'approved':
            print(f"\n✅ Pagamento APROVADO! Atualizando financeiro...")
            
            # Calcular próxima cobrança
            data_vencimento_atual = financeiro.data_proxima_cobranca
            dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10
            
            if data_vencimento_atual.month == 12:
                proximo_mes = 1
                proximo_ano = data_vencimento_atual.year + 1
            else:
                proximo_mes = data_vencimento_atual.month + 1
                proximo_ano = data_vencimento_atual.year
            
            ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
            dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
            proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
            
            # Atualizar financeiro
            financeiro.status_pagamento = 'ativo'
            financeiro.ultimo_pagamento = timezone.now()
            financeiro.data_proxima_cobranca = proxima_cobranca
            financeiro.save(update_fields=['status_pagamento', 'ultimo_pagamento', 'data_proxima_cobranca'])
            
            print(f"✅ Financeiro atualizado!")
            print(f"   Status: {financeiro.status_pagamento}")
            print(f"   Último pagamento: {financeiro.ultimo_pagamento}")
            print(f"   Próxima cobrança: {financeiro.data_proxima_cobranca}")
            
            # Verificar se senha foi enviada
            if not financeiro.senha_enviada:
                print(f"\n📧 Enviando senha provisória...")
                from superadmin.email_service import EmailService
                service = EmailService()
                owner = loja.owner
                success = service.enviar_senha_provisoria(loja, owner)
                
                if success:
                    print(f"✅ Senha enviada para {owner.email}")
                else:
                    print(f"⚠️ Falha ao enviar senha (registrado para retry)")
            else:
                print(f"ℹ️ Senha já foi enviada em {financeiro.data_envio_senha}")
        
        elif status_mp == 'pending':
            print(f"⏳ Pagamento ainda pendente no Mercado Pago")
        
        else:
            print(f"⚠️ Status não reconhecido: {status_mp}")
    
    except Exception as e:
        print(f"❌ Erro ao processar loja {loja.slug}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print(f"FIM DA ATUALIZAÇÃO")
print(f"{'='*80}\n")
