#!/usr/bin/env python3
"""
Script para testar manualmente a integração Asaas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.asaas_service import LojaAsaasService

def testar_integracao():
    print("=== Testando Integração Asaas ===")
    
    # Buscar a loja criada
    try:
        loja = Loja.objects.get(slug='loja-nova-asaas')
        financeiro = loja.financeiro
        
        print(f"✅ Loja encontrada: {loja.nome}")
        print(f"✅ Financeiro ID: {financeiro.id}")
        print(f"✅ Valor mensalidade: R$ {financeiro.valor_mensalidade}")
        print(f"✅ Status atual: {financeiro.status_pagamento}")
        
        # Verificar se já tem dados Asaas
        if financeiro.asaas_customer_id:
            print(f"⚠️ Loja já tem customer_id: {financeiro.asaas_customer_id}")
            return
        
        # Testar serviço Asaas
        service = LojaAsaasService()
        print(f"✅ Serviço disponível: {service.available}")
        
        if not service.available:
            print("❌ Serviço Asaas não disponível")
            return
        
        # Testar criação de cobrança
        print("\n=== Criando cobrança no Asaas ===")
        resultado = service.criar_cobranca_loja(loja, financeiro)
        
        if resultado.get('success'):
            print(f"✅ Cobrança criada com sucesso!")
            print(f"✅ Customer ID: {resultado.get('customer_id')}")
            print(f"✅ Payment ID: {resultado.get('payment_id')}")
            print(f"✅ Valor: R$ {resultado.get('value')}")
            print(f"✅ Vencimento: {resultado.get('due_date')}")
            print(f"✅ Boleto URL: {resultado.get('boleto_url')}")
            
            # Verificar se os dados foram salvos
            financeiro.refresh_from_db()
            print(f"\n=== Dados salvos no financeiro ===")
            print(f"✅ Customer ID salvo: {financeiro.asaas_customer_id}")
            print(f"✅ Payment ID salvo: {financeiro.asaas_payment_id}")
            print(f"✅ Boleto URL salva: {financeiro.boleto_url}")
            
        else:
            print(f"❌ Erro na cobrança: {resultado.get('error')}")
            
    except Loja.DoesNotExist:
        print("❌ Loja 'loja-nova-asaas' não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_integracao()