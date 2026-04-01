#!/usr/bin/env python3
"""
Script para consultar serviços municipais disponíveis no Asaas

Uso:
    python consultar_servicos_asaas.py
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

def main():
    print("🔍 Consultando serviços municipais no Asaas...")
    print("=" * 80)
    print()
    
    # Obter configuração
    config = AsaasConfig.get_config()
    if not config.enabled or not config.api_key:
        print("❌ Asaas não configurado")
        return
    
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    try:
        # Consultar serviços municipais
        print("📋 Consultando lista de serviços municipais...")
        print()
        
        # Endpoint para listar serviços (pode variar conforme API)
        response = client._make_request('GET', 'municipalServices', {})
        
        if isinstance(response, list):
            print(f"✅ {len(response)} serviços encontrados")
            print()
            
            # Filtrar serviços relacionados a software/computadores
            keywords = ['software', 'computador', 'informática', 'sistema', 'manutenção', '14.01', '1401']
            
            print("🔍 Serviços relacionados a software/computadores:")
            print()
            
            for service in response:
                code = service.get('code', '')
                name = service.get('name', '')
                service_id = service.get('id', '')
                
                # Verificar se contém alguma palavra-chave
                text = f"{code} {name}".lower()
                if any(keyword.lower() in text for keyword in keywords):
                    print(f"ID: {service_id}")
                    print(f"Código: {code}")
                    print(f"Nome: {name}")
                    print("-" * 80)
            
            print()
            print("💡 Para usar um serviço, configure:")
            print("   ASAAS_INVOICE_SERVICE_ID=<id_do_servico>")
            
        else:
            print("⚠️  Resposta inesperada da API:")
            print(response)
    
    except Exception as e:
        print(f"❌ Erro ao consultar serviços: {e}")
        print()
        print("💡 A API do Asaas pode não ter endpoint público para listar serviços.")
        print("   Consulte a documentação ou o suporte do Asaas para obter o ID correto.")
        print()
        print("📖 Documentação: https://docs.asaas.com/reference/criar-nota-fiscal")

if __name__ == "__main__":
    main()
