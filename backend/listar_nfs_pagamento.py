"""
Script para listar todas as NFs de um pagamento

Payment ID: pay_saj2jh0wvp5cban7
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

def listar_nfs():
    """Lista todas as NFs de um pagamento"""
    
    # Configurar cliente Asaas
    config = AsaasConfig.get_config()
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    payment_id = 'pay_saj2jh0wvp5cban7'
    
    logger.info(f"Listando NFs do pagamento: {payment_id}")
    
    try:
        # Listar NFs (endpoint não documentado, vamos tentar)
        endpoint = f'invoices?payment={payment_id}'
        result = client._make_request('GET', endpoint)
        
        logger.info(f"Resultado: {result}")
        
        if result.get('data'):
            for nf in result['data']:
                logger.info(f"NF ID: {nf.get('id')}, Status: {nf.get('status')}, Valor: {nf.get('value')}")
        else:
            logger.info("Nenhuma NF encontrada")
            
    except Exception as e:
        logger.error(f"Erro ao listar NFs: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    listar_nfs()
