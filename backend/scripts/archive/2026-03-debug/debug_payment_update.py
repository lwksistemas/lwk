#!/usr/bin/env python
"""
Script para debugar atualização de pagamento
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, LojaAssinatura
from superadmin.models import Loja, FinanceiroLoja
from superadmin.sync_service import AsaasSyncService
from datetime import date

# Buscar loja "Luiz Salao"
loja_slug = 'luiz-salao-5889'

print(f"\n{'='*60}")
print(f"DEBUG: Atualização de Pagamento - Loja {loja_slug}")
print(f"{'='*60}\n")

try:
    loja = Loja.objects.get(slug=loja_slug, is_active=True)
    print(f"✅ Loja encontrada: {loja.nome}")
    print(f"   - Slug: {loja.slug}")
    print(f"   - Owner: {loja.owner.email}")
    print(f"   - Plano: {loja.plano.nome}")
    print(f"   - Tipo Assinatura: {loja.get_tipo_assinatura_display()}")
except Loja.DoesNotExist:
    print(f"❌ Loja {loja_slug} não encontrada")
    exit(1)

# Buscar financeiro
try:
    financeiro = loja.financeiro
    print(f"\n📊 Financeiro:")
    print(f"   - Status: {financeiro.status_pagamento}")
    print(f"   - Último Pagamento: {financeiro.ultimo_pagamento}")
    print(f"   - Próxima Cobrança: {financeiro.data_proxima_cobranca}")
    print(f"   - Dia Vencimento: {financeiro.dia_vencimento}")
except Exception as e:
    print(f"❌ Erro ao buscar financeiro: {e}")
    exit(1)

# Buscar assinatura Asaas
try:
    assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
    print(f"\n💳 Assinatura Asaas:")
    print(f"   - Customer ID: {assinatura.asaas_customer.asaas_id}")
    print(f"   - Data Vencimento: {assinatura.data_vencimento}")
    print(f"   - Plano: {assinatura.plano_nome}")
    print(f"   - Valor: R$ {assinatura.plano_valor}")
    print(f"   - Ativa: {assinatura.ativa}")
except LojaAssinatura.DoesNotExist:
    print(f"❌ Assinatura Asaas não encontrada")
    exit(1)

# Buscar pagamento atual
if assinatura.current_payment:
    payment = assinatura.current_payment
    print(f"\n💰 Pagamento Atual:")
    print(f"   - Asaas ID: {payment.asaas_id}")
    print(f"   - Status: {payment.status}")
    print(f"   - Valor: R$ {payment.value}")
    print(f"   - Vencimento: {payment.due_date}")
    print(f"   - External Reference: {payment.external_reference}")
    print(f"   - Data Pagamento: {payment.payment_date}")
else:
    print(f"\n❌ Nenhum pagamento atual encontrado")
    exit(1)

# Verificar se o pagamento está pago
if payment.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
    print(f"\n✅ Pagamento está PAGO (status: {payment.status})")
    
    # Testar método _get_loja_from_payment
    sync_service = AsaasSyncService()
    loja_from_payment = sync_service._get_loja_from_payment(payment)
    
    if loja_from_payment:
        print(f"✅ Loja identificada pelo pagamento: {loja_from_payment.nome}")
    else:
        print(f"❌ Não foi possível identificar a loja pelo pagamento")
        print(f"   - Verificando external_reference: {payment.external_reference}")
        if payment.external_reference and 'loja_' in payment.external_reference:
            extracted_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '')
            print(f"   - Slug extraído: {extracted_slug}")
        exit(1)
    
    # Calcular próxima data de cobrança
    hoje = date.today()
    dia_vencimento = financeiro.dia_vencimento
    
    from calendar import monthrange
    if hoje.month == 12:
        proximo_mes = 1
        proximo_ano = hoje.year + 1
    else:
        proximo_mes = hoje.month + 1
        proximo_ano = hoje.year
    
    ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
    dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
    proxima_data_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
    
    print(f"\n📅 Cálculo de Próxima Cobrança:")
    print(f"   - Hoje: {hoje}")
    print(f"   - Dia Vencimento: {dia_vencimento}")
    print(f"   - Próximo Mês: {proximo_mes}/{proximo_ano}")
    print(f"   - Próxima Cobrança Calculada: {proxima_data_cobranca}")
    print(f"   - Próxima Cobrança Atual (DB): {financeiro.data_proxima_cobranca}")
    
    # Verificar se já existe cobrança para essa data
    cobranca_existente = AsaasPayment.objects.filter(
        customer=assinatura.asaas_customer,
        due_date=proxima_data_cobranca,
        status__in=['PENDING', 'RECEIVED', 'CONFIRMED']
    )
    
    print(f"\n🔍 Verificação de Duplicação:")
    print(f"   - Cobranças existentes para {proxima_data_cobranca}: {cobranca_existente.count()}")
    
    if cobranca_existente.exists():
        print(f"   ⚠️ JÁ EXISTE cobrança para essa data!")
        for cob in cobranca_existente:
            print(f"      - ID: {cob.asaas_id}, Status: {cob.status}, Valor: R$ {cob.value}")
    else:
        print(f"   ✅ Nenhuma cobrança existente, pode criar nova")
    
    # Simular atualização
    print(f"\n🔄 Simulando atualização...")
    print(f"   - Atualizar financeiro.data_proxima_cobranca: {financeiro.data_proxima_cobranca} → {proxima_data_cobranca}")
    print(f"   - Atualizar assinatura.data_vencimento: {assinatura.data_vencimento} → {proxima_data_cobranca}")
    
    if not cobranca_existente.exists():
        print(f"   - Criar novo boleto no Asaas com vencimento: {proxima_data_cobranca}")
    
    # Perguntar se quer executar
    resposta = input(f"\n❓ Executar atualização? (s/n): ")
    
    if resposta.lower() == 's':
        print(f"\n🚀 Executando atualização...")
        resultado = sync_service._update_loja_financeiro_from_payment(payment)
        
        if resultado:
            print(f"✅ Atualização executada com sucesso!")
            
            # Recarregar dados
            financeiro.refresh_from_db()
            assinatura.refresh_from_db()
            
            print(f"\n📊 Dados Atualizados:")
            print(f"   - Financeiro.data_proxima_cobranca: {financeiro.data_proxima_cobranca}")
            print(f"   - Assinatura.data_vencimento: {assinatura.data_vencimento}")
            
            # Verificar se novo boleto foi criado
            novos_boletos = AsaasPayment.objects.filter(
                customer=assinatura.asaas_customer,
                due_date=proxima_data_cobranca
            )
            
            if novos_boletos.exists():
                print(f"\n✅ Novo boleto criado:")
                for boleto in novos_boletos:
                    print(f"   - ID: {boleto.asaas_id}")
                    print(f"   - Status: {boleto.status}")
                    print(f"   - Valor: R$ {boleto.value}")
                    print(f"   - Vencimento: {boleto.due_date}")
            else:
                print(f"\n❌ Nenhum novo boleto foi criado")
        else:
            print(f"❌ Erro na atualização")
    else:
        print(f"\n❌ Atualização cancelada")
else:
    print(f"\n⚠️ Pagamento NÃO está pago (status: {payment.status})")
    print(f"   - Não é necessário atualizar")

print(f"\n{'='*60}\n")
