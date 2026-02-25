#!/usr/bin/env python
"""
Script para corrigir financeiro da Clinica Felipe
Executar: heroku run python backend/fix_clinica_felipe.py --app lwksistemas
"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja, MercadoPagoConfig
from superadmin.mercadopago_service import MercadoPagoClient
from django.utils import timezone
from datetime import date
from calendar import monthrange

print(f"\n{'='*80}")
print(f"CORREÇÃO: Clinica Felipe - Mercado Pago")
print(f"{'='*80}\n")

try:
    loja = Loja.objects.get(slug='clinica-felipe-5898')
    financeiro = loja.financeiro
    
    print(f"📋 DADOS ATUAIS")
    print(f"   Loja: {loja.nome}")
    print(f"   Status: {financeiro.status_pagamento}")
    print(f"   Senha enviada: {financeiro.senha_enviada}")
    print(f"   Boleto ID: {financeiro.mercadopago_payment_id}")
    print(f"   PIX ID: {financeiro.mercadopago_pix_payment_id}")
    
    # Verificar status no Mercado Pago
    config = MercadoPagoConfig.get_config()
    if not config or not config.access_token:
        print("\n❌ Mercado Pago não configurado")
        sys.exit(1)
    
    client = MercadoPagoClient(config.access_token)
    
    # Verificar PIX (ID da transação: 147733399216)
    print(f"\n🔍 CONSULTANDO API DO MERCADO PAGO")
    
    pagamento_aprovado = None
    payment_id_aprovado = None
    
    # Verificar PIX
    if financeiro.mercadopago_pix_payment_id:
        print(f"\n   Verificando PIX: {financeiro.mercadopago_pix_payment_id}")
        pix_data = client.get_payment(str(financeiro.mercadopago_pix_payment_id))
        if pix_data:
            status_pix = pix_data.get('status', '')
            print(f"   Status PIX: {status_pix}")
            print(f"   Valor: R$ {pix_data.get('transaction_amount', 0)}")
            print(f"   Data aprovação: {pix_data.get('date_approved', 'N/A')}")
            if status_pix == 'approved':
                pagamento_aprovado = pix_data
                payment_id_aprovado = financeiro.mercadopago_pix_payment_id
                print(f"   ✅ PIX APROVADO!")
    
    # Verificar Boleto
    if financeiro.mercadopago_payment_id and not pagamento_aprovado:
        print(f"\n   Verificando Boleto: {financeiro.mercadopago_payment_id}")
        boleto_data = client.get_payment(str(financeiro.mercadopago_payment_id))
        if boleto_data:
            status_boleto = boleto_data.get('status', '')
            print(f"   Status Boleto: {status_boleto}")
            if status_boleto == 'approved':
                pagamento_aprovado = boleto_data
                payment_id_aprovado = financeiro.mercadopago_payment_id
                print(f"   ✅ BOLETO APROVADO!")
    
    if not pagamento_aprovado:
        print(f"\n⚠️ Nenhum pagamento aprovado encontrado")
        print(f"   Aguarde alguns minutos e tente novamente")
        sys.exit(0)
    
    print(f"\n{'='*80}")
    print(f"ATUALIZANDO FINANCEIRO")
    print(f"{'='*80}")
    
    # Calcular próxima cobrança usando dia_vencimento
    dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10
    hoje = date.today()
    
    # Calcular próximo mês
    if hoje.month == 12:
        proximo_mes = 1
        proximo_ano = hoje.year + 1
    else:
        proximo_mes = hoje.month + 1
        proximo_ano = hoje.year
    
    ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
    dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
    proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
    
    # Atualizar financeiro
    financeiro.status_pagamento = 'ativo'
    financeiro.ultimo_pagamento = timezone.now()
    financeiro.data_proxima_cobranca = proxima_cobranca
    financeiro.save()
    
    print(f"\n✅ Financeiro atualizado!")
    print(f"   Status: {financeiro.status_pagamento}")
    print(f"   Último pagamento: {financeiro.ultimo_pagamento}")
    print(f"   Próxima cobrança: {financeiro.data_proxima_cobranca}")
    print(f"   Dia vencimento fixo: {dia_vencimento}")
    
    # Recarregar do banco
    financeiro.refresh_from_db()
    
    # Enviar senha provisória
    print(f"\n{'='*80}")
    print(f"ENVIANDO SENHA PROVISÓRIA")
    print(f"{'='*80}")
    
    if financeiro.senha_enviada:
        print(f"\nℹ️ Senha já foi enviada em {financeiro.data_envio_senha}")
        print(f"   Pulando envio")
    else:
        print(f"\n📧 Enviando senha para {loja.owner.email}...")
        
        from superadmin.email_service import EmailService
        service = EmailService()
        owner = loja.owner
        
        success = service.enviar_senha_provisoria(loja, owner)
        
        if success:
            print(f"✅ Senha enviada com sucesso!")
            print(f"   Email: {owner.email}")
            print(f"   Verificar caixa de entrada")
        else:
            print(f"⚠️ Falha ao enviar senha")
            print(f"   Email foi registrado para retry automático")
            print(f"   Ou use o botão '📧 Reenviar senha' no painel")
    
    print(f"\n{'='*80}")
    print(f"CORREÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"{'='*80}")
    print(f"\n✅ Status: Ativo")
    print(f"✅ Pagamento: Registrado")
    print(f"✅ Próxima cobrança: {proxima_cobranca.strftime('%d/%m/%Y')}")
    print(f"✅ Senha: {'Enviada' if financeiro.senha_enviada else 'Registrada para envio'}")
    print(f"\n{'='*80}\n")
    
except Loja.DoesNotExist:
    print(f"\n❌ ERRO: Loja 'clinica-felipe-5898' não encontrada")
    print(f"   Verificar se o slug está correto\n")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n")
    sys.exit(1)
