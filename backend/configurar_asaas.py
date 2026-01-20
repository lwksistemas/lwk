#!/usr/bin/env python3
"""
Script para configurar Asaas automaticamente
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from asaas_integration.models import AsaasConfig

def configurar_asaas():
    """Configurar Asaas com a chave do usuário"""
    
    # Chave API do usuário (sandbox)
    api_key = '$aact_hmlg_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjY5ZjZhMmI3LTFmZWYtNDdkMC1iMmVkLTY4NWU0NzkxMmJlZDo6JGFhY2hfODYyMDJjYWYtZjY5Ny00OWM4LWI5NWItYmRmMjNjNDVkYmQ4'
    
    try:
        # Obter ou criar configuração
        config = AsaasConfig.get_config()
        
        # Configurar
        config.api_key = api_key
        config.enabled = True
        config.save()  # O sandbox será detectado automaticamente
        
        print("✅ Asaas configurado com sucesso!")
        print(f"   - API Key: {config.api_key_masked}")
        print(f"   - Ambiente: {config.environment_name}")
        print(f"   - Habilitado: {config.enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Asaas: {e}")
        return False

if __name__ == "__main__":
    configurar_asaas()