"""
Script para cancelar NF com erro e reemitir com código correto

Loja: Felix Representações (41449198000172)
Payment ID: pay_saj2jh0wvp5cban7
Invoice ID anterior: inv_000018412613
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja
from asaas_integration.invoice_service import emitir_nf_para_pagamento
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cancelar_e_reemitir_nf():
    """Cancela NF anterior e reemite com código correto"""
    
    # Configurar cliente Asaas
    config = AsaasConfig.get_config()
    client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
    
    # IDs
    payment_id_pago = 'pay_saj2jh0wvp5cban7'
    invoice_id_anterior = 'inv_000018412613'
    
    # Buscar loja
    loja = Loja.objects.get(slug='41449198000172')
    
    logger.info(f"Loja: {loja.nome}")
    logger.info(f"Payment ID: {payment_id_pago}")
    logger.info(f"Invoice ID anterior: {invoice_id_anterior}")
    
    # 1. Cancelar NF anterior
    logger.info("Cancelando NF anterior...")
    try:
        result = client.cancel_invoice(invoice_id_anterior)
        logger.info(f"✅ NF anterior cancelada: {result}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao cancelar NF (pode já estar cancelada): {e}")
    
    # 2. Emitir nova NF com código correto
    logger.info("Emitindo nova NF com código correto (0107)...")
    
    try:
        result = emitir_nf_para_pagamento(
            asaas_payment_id=payment_id_pago,
            loja=loja,
            value=8.0,
            description=f"Assinatura {loja.plano.nome} (Mensal) - Loja {loja.nome}",
            send_email=True
        )
        
        if result.get('success'):
            logger.info(f"✅ NF emitida com sucesso!")
            logger.info(f"Invoice ID: {result.get('invoice_id')}")
            logger.info(f"Email enviado: {result.get('email_sent')}")
        else:
            logger.error(f"❌ Falha ao emitir NF: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro ao emitir NF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    cancelar_e_reemitir_nf()
