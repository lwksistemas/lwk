"""
Script para atualizar código de serviço da NF com erro

Invoice ID: inv_000018412613
Código antigo: 01.07 (com ponto)
Código novo: 0107 (sem ponto)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def atualizar_codigo_nf():
    """Atualiza código de serviço da NF"""
    
    # Configurar cliente Asaas
    config = AsaasConfig.get_config()
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    invoice_id = 'inv_000018412613'
    
    logger.info(f"Atualizando código de serviço da NF: {invoice_id}")
    
    try:
        # Atualizar NF
        endpoint = f'invoices/{invoice_id}'
        data = {
            'municipalServiceCode': '0107',  # Sem ponto
            'municipalServiceName': 'Software sob demanda / Assinatura de sistema',
        }
        
        result = client._make_request('PUT', endpoint, data)
        logger.info(f"✅ NF atualizada: {result}")
        
        # Tentar autorizar novamente
        logger.info("Tentando autorizar NF novamente...")
        auth_result = client.authorize_invoice(invoice_id)
        logger.info(f"✅ NF autorizada: {auth_result}")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    atualizar_codigo_nf()
