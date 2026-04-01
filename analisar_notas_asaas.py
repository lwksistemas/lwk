#!/usr/bin/env python3
"""
Script para analisar notas fiscais emitidas no Asaas
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
import json

def main():
    print("🔍 Analisando notas fiscais no Asaas...")
    print("=" * 80)
    print()
    
    # Obter configuração
    config = AsaasConfig.get_config()
    if not config.enabled or not config.api_key:
        print("❌ Asaas não configurado")
        return
    
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    try:
        # Buscar últimas notas fiscais
        print("📋 Buscando últimas notas fiscais...")
        print()
        
        response = client._make_request('GET', 'invoices', {'limit': 10, 'offset': 0})
        invoices = response.get('data', [])
        
        if not invoices:
            print("❌ Nenhuma nota fiscal encontrada")
            return
        
        print(f"✅ Encontradas {len(invoices)} notas fiscais")
        print()
        
        for i, inv in enumerate(invoices, 1):
            print(f"{'='*80}")
            print(f"NOTA FISCAL #{i}")
            print(f"{'='*80}")
            print(f"ID: {inv.get('id')}")
            print(f"Status: {inv.get('status')}")
            print(f"Valor: R$ {inv.get('value')}")
            print(f"Data Efetiva: {inv.get('effectiveDate')}")
            print()
            print(f"📋 CAMPOS MUNICIPAIS:")
            print(f"   municipalServiceCode: {inv.get('municipalServiceCode')}")
            print(f"   municipalServiceId: {inv.get('municipalServiceId')}")
            print(f"   municipalServiceName: {inv.get('municipalServiceName')}")
            print()
            print(f"📝 DESCRIÇÃO:")
            print(f"   {inv.get('serviceDescription')}")
            print()
            
            # Mostrar JSON completo da nota
            if i == 1:  # Apenas para a primeira nota
                print(f"📄 JSON COMPLETO DA ÚLTIMA NOTA:")
                print(json.dumps(inv, indent=2, ensure_ascii=False))
            
            print()
            
    except Exception as e:
        print(f"❌ Erro ao consultar notas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
