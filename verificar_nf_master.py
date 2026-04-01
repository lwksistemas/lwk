#!/usr/bin/env python3
"""
Script para verificar status de pagamento e nota fiscal da Master Representações

Uso:
    python verificar_nf_master.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, PagamentoLoja, FinanceiroLoja
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
from datetime import datetime

def main():
    print("🔍 Verificando status da Master Representações...")
    print("=" * 80)
    print()
    
    # Buscar loja Master
    try:
        loja = Loja.objects.get(nome__icontains='Master')
        print(f"✅ Loja encontrada: {loja.nome}")
        print(f"   CNPJ: {loja.cpf_cnpj}")
        print(f"   Owner: {loja.owner.email}")
        print()
    except Loja.DoesNotExist:
        print("❌ Loja Master não encontrada")
        return
    except Loja.MultipleObjectsReturned:
        lojas = Loja.objects.filter(nome__icontains='Master')
        print(f"⚠️  Múltiplas lojas encontradas:")
        for l in lojas:
            print(f"   - {l.nome} ({l.cpf_cnpj})")
        print()
        loja = lojas.first()
        print(f"✅ Usando: {loja.nome}")
        print()
    
    # Buscar financeiro
    try:
        financeiro = FinanceiroLoja.objects.get(loja=loja)
        print("💰 FINANCEIRO")
        print(f"   Status: {financeiro.status_pagamento}")
        print(f"   Próxima cobrança: {financeiro.data_proxima_cobranca}")
        print(f"   Valor: R$ {financeiro.valor_mensalidade}")
        print(f"   Asaas Payment ID: {financeiro.asaas_payment_id}")
        print()
    except FinanceiroLoja.DoesNotExist:
        print("❌ Financeiro não encontrado")
        return
    
    # Buscar pagamentos
    pagamentos = PagamentoLoja.objects.filter(loja=loja).order_by('-created_at')[:5]
    
    print("📋 PAGAMENTOS RECENTES")
    if not pagamentos:
        print("   Nenhum pagamento encontrado")
    else:
        for pag in pagamentos:
            print(f"   - {pag.referencia_mes.strftime('%m/%Y')}: R$ {pag.valor} - {pag.status}")
            print(f"     Vencimento: {pag.data_vencimento}")
            if pag.asaas_payment_id:
                print(f"     Asaas ID: {pag.asaas_payment_id}")
            if pag.data_pagamento:
                print(f"     Pago em: {pag.data_pagamento}")
    print()
    
    # Verificar no Asaas
    config = AsaasConfig.get_config()
    if not config.enabled or not config.api_key:
        print("⚠️  Asaas não configurado")
        return
    
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    print("🔍 VERIFICANDO NO ASAAS...")
    print()
    
    # Verificar payment atual
    if financeiro.asaas_payment_id:
        try:
            payment = client.get_payment(financeiro.asaas_payment_id)
            print("💳 COBRANÇA ATUAL")
            print(f"   ID: {payment.get('id')}")
            print(f"   Status: {payment.get('status')}")
            print(f"   Valor: R$ {payment.get('value')}")
            print(f"   Vencimento: {payment.get('dueDate')}")
            print(f"   Cliente: {payment.get('customer')}")
            
            # Verificar se tem nota fiscal
            if payment.get('status') == 'CONFIRMED':
                print()
                print("✅ PAGAMENTO CONFIRMADO!")
                print()
                
                # Buscar notas fiscais
                try:
                    invoices = client.list_invoices(payment_id=financeiro.asaas_payment_id)
                    
                    if invoices:
                        print("📄 NOTAS FISCAIS")
                        for inv in invoices:
                            print(f"   ID: {inv.get('id')}")
                            print(f"   Status: {inv.get('status')}")
                            print(f"   Código Serviço: {inv.get('municipalServiceCode')}")
                            print(f"   Nome Serviço: {inv.get('municipalServiceName')}")
                            print(f"   Valor: R$ {inv.get('value')}")
                            
                            if inv.get('status') == 'AUTHORIZED':
                                print(f"   ✅ NOTA FISCAL EMITIDA!")
                                if inv.get('invoiceUrl'):
                                    print(f"   🔗 URL: {inv.get('invoiceUrl')}")
                            elif inv.get('status') == 'ERROR':
                                print(f"   ❌ ERRO NA EMISSÃO")
                                print(f"   Motivo: {inv.get('statusDescription')}")
                            print()
                    else:
                        print("⚠️  Nenhuma nota fiscal encontrada para este pagamento")
                        print("   A nota pode estar sendo processada...")
                        
                except Exception as e:
                    print(f"⚠️  Erro ao buscar notas fiscais: {e}")
            
            elif payment.get('status') == 'PENDING':
                print()
                print("⏳ Aguardando confirmação do pagamento...")
                print("   A nota fiscal será emitida automaticamente após a confirmação.")
            
            print()
            
        except Exception as e:
            print(f"❌ Erro ao buscar payment no Asaas: {e}")
    else:
        print("⚠️  Nenhum payment ID configurado no financeiro")
    
    print()
    print("=" * 80)
    print("✅ Verificação concluída")

if __name__ == "__main__":
    main()
