#!/usr/bin/env python3
"""
Script para verificar status do pagamento e nota fiscal - Felix Representações
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
from superadmin.models import Loja
import json

def main():
    print("🔍 Verificando status - Felix Representações")
    print("=" * 80)
    print()
    
    # Obter configuração
    config = AsaasConfig.get_config()
    if not config.enabled or not config.api_key:
        print("❌ Asaas não configurado")
        return
    
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    # Buscar loja Felix
    try:
        loja = Loja.objects.get(nome__icontains='Felix')
        print(f"✅ Loja encontrada: {loja.nome}")
        print(f"   CNPJ: {loja.cnpj}")
        print(f"   Customer ID: {loja.asaas_customer_id}")
        print()
    except Loja.DoesNotExist:
        print("❌ Loja Felix não encontrada")
        return
    
    # Buscar pagamentos da loja
    try:
        print("📋 Buscando pagamentos...")
        response = client._make_request('GET', 'payments', {
            'customer': loja.asaas_customer_id,
            'limit': 5
        })
        
        payments = response.get('data', [])
        
        if not payments:
            print("❌ Nenhum pagamento encontrado")
            return
        
        print(f"✅ Encontrados {len(payments)} pagamentos")
        print()
        
        for i, payment in enumerate(payments, 1):
            print(f"{'='*80}")
            print(f"PAGAMENTO #{i}")
            print(f"{'='*80}")
            print(f"ID: {payment.get('id')}")
            print(f"Status: {payment.get('status')}")
            print(f"Valor: R$ {payment.get('value')}")
            print(f"Vencimento: {payment.get('dueDate')}")
            print(f"Descrição: {payment.get('description')}")
            
            # Se pago, verificar nota fiscal
            if payment.get('status') in ['RECEIVED', 'CONFIRMED']:
                print()
                print("💰 PAGAMENTO CONFIRMADO!")
                print()
                
                # Buscar nota fiscal
                try:
                    print("📋 Buscando nota fiscal...")
                    inv_response = client._make_request('GET', 'invoices', {
                        'payment': payment.get('id')
                    })
                    
                    invoices = inv_response.get('data', [])
                    
                    if invoices:
                        for inv in invoices:
                            print()
                            print(f"📄 NOTA FISCAL:")
                            print(f"   ID: {inv.get('id')}")
                            print(f"   Status: {inv.get('status')}")
                            print(f"   Valor: R$ {inv.get('value')}")
                            print(f"   Data: {inv.get('effectiveDate')}")
                            print()
                            print(f"   🏛️ CAMPOS MUNICIPAIS:")
                            print(f"      municipalServiceId: {inv.get('municipalServiceId')}")
                            print(f"      municipalServiceCode: {inv.get('municipalServiceCode')}")
                            print(f"      municipalServiceName: {inv.get('municipalServiceName')}")
                            
                            if inv.get('status') == 'AUTHORIZED':
                                print()
                                print("   ✅ NOTA FISCAL AUTORIZADA COM SUCESSO!")
                            elif inv.get('status') == 'ERROR':
                                print()
                                print("   ❌ ERRO NA EMISSÃO:")
                                print(f"      {inv.get('statusDescription')}")
                    else:
                        print()
                        print("⏳ Nota fiscal ainda não foi emitida")
                        print("   Aguarde alguns minutos...")
                        
                except Exception as e:
                    print(f"❌ Erro ao buscar nota fiscal: {e}")
            else:
                print()
                print(f"⏳ Aguardando confirmação do pagamento (Status: {payment.get('status')})")
            
            print()
            
    except Exception as e:
        print(f"❌ Erro ao buscar pagamentos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
