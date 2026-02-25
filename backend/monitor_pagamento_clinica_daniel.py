#!/usr/bin/env python
"""
Script para monitorar pagamento da Clinica Daniel em tempo real
Executar: heroku run python backend/monitor_pagamento_clinica_daniel.py --app lwksistemas
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
from datetime import datetime

print(f"\n{'='*80}")
print(f"MONITORAMENTO: Pagamento Clinica Daniel")
print(f"Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"{'='*80}\n")

try:
    loja = Loja.objects.get(slug='clinica-daniel-5889')
    financeiro = loja.financeiro
    
    print(f"📋 DADOS DA LOJA")
    print(f"   Nome: {loja.nome}")
    print(f"   Slug: {loja.slug}")
    print(f"   Email: {loja.owner.email}")
    print(f"   Provedor: {financeiro.provedor_boleto}")
    print(f"   Criada em: {loja.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
    
    print(f"\n💰 FINANCEIRO")
    print(f"   Status: {financeiro.status_pagamento}")
    print(f"   Valor: R$ {financeiro.valor_mensalidade}")
    print(f"   Vencimento: {financeiro.data_proxima_cobranca.strftime('%d/%m/%Y')}")
    print(f"   Total pagamentos: {financeiro.total_pagamentos}")
    
    print(f"\n🔑 MERCADO PAGO IDs")
    print(f"   Boleto Payment ID: {financeiro.mercadopago_payment_id or 'N/A'}")
    print(f"   PIX Payment ID: {financeiro.mercadopago_pix_payment_id or 'N/A'}")
    
    print(f"\n📧 SENHA PROVISÓRIA")
    print(f"   Senha enviada: {financeiro.senha_enviada}")
    if financeiro.data_envio_senha:
        print(f"   Data envio: {financeiro.data_envio_senha.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        print(f"   Data envio: Ainda não enviada")
    
    print(f"\n📅 HISTÓRICO DE PAGAMENTOS")
    if financeiro.data_ultimo_pagamento:
        print(f"   Último pagamento: {financeiro.data_ultimo_pagamento.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        print(f"   Último pagamento: Nenhum pagamento registrado")
    
    print(f"\n🔗 LINKS")
    print(f"   Boleto: {financeiro.boleto_url[:60] if financeiro.boleto_url else 'N/A'}...")
    print(f"   PIX QR Code: {'Disponível' if financeiro.pix_qr_code else 'N/A'}")
    print(f"   PIX Copy/Paste: {'Disponível' if financeiro.pix_copy_paste else 'N/A'}")
    
    print(f"\n{'='*80}")
    
    if financeiro.status_pagamento == 'ativo' and financeiro.senha_enviada:
        print(f"✅ PAGAMENTO PROCESSADO COM SUCESSO!")
        print(f"   Status: Ativo")
        print(f"   Senha enviada: Sim")
        print(f"   Sistema funcionando 100%")
    elif financeiro.status_pagamento == 'ativo' and not financeiro.senha_enviada:
        print(f"⚠️ PAGAMENTO PROCESSADO MAS SENHA NÃO ENVIADA")
        print(f"   Status: Ativo")
        print(f"   Senha enviada: Não")
        print(f"   Ação: Verificar logs ou usar botão 'Reenviar senha'")
    else:
        print(f"⏳ AGUARDANDO PAGAMENTO")
        print(f"   Status: {financeiro.status_pagamento}")
        print(f"   Aguardando confirmação do Mercado Pago")
    
    print(f"{'='*80}\n")
    
except Loja.DoesNotExist:
    print(f"❌ ERRO: Loja 'clinica-daniel-5889' não encontrada")
    print(f"   Verificar se o slug está correto")
    print(f"\n")
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n")
