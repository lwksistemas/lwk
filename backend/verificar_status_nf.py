"""
Script para verificar status da NF

Invoice ID: inv_000018413423
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verificar_status_nf():
    """Verifica status da NF"""
    
    # Configurar cliente Asaas
    config = AsaasConfig.get_config()
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    invoice_id = 'inv_000018414220'
    
    logger.info(f"Verificando status da NF: {invoice_id}")
    
    try:
        result = client.get_invoice(invoice_id)
        
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Status Description: {result.get('statusDescription')}")
        logger.info(f"Código de serviço: {result.get('municipalServiceCode')}")
        logger.info(f"Nome do serviço: {result.get('municipalServiceName')}")
        
        logger.info(f"\nDetalhes completos:")
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    verificar_status_nf()
