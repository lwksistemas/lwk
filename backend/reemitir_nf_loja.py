"""
Script para reemitir nota fiscal após correção do CEP

Loja: Felix Representações (41449198000172)
Payment ID: pay_saj2jh0wvp5cban7
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja
from asaas_integration.invoice_service import emitir_nf_para_pagamento
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reemitir_nf():
    """Reemite NF para pagamento já confirmado"""
    
    # Payment ID do boleto PAGO (não o novo boleto)
    payment_id_pago = 'pay_saj2jh0wvp5cban7'
    
    # Buscar loja
    loja = Loja.objects.get(slug='41449198000172')
    fin = loja.financeiro
    
    logger.info(f"Loja: {loja.nome}")
    logger.info(f"Payment ID do boleto PAGO: {payment_id_pago}")
    logger.info(f"Payment ID atual no financeiro: {fin.asaas_payment_id}")
    logger.info(f"Status: {fin.status_pagamento}")
    
    # Verificar se pagamento foi confirmado
    if fin.status_pagamento != 'ativo':
        logger.warning(f"Pagamento não está ativo: {fin.status_pagamento}")
        logger.info("Atualizando status para 'ativo'...")
        fin.status_pagamento = 'ativo'
        fin.save()
    
    # Emitir NF para o boleto PAGO
    logger.info(f"Emitindo NF para payment {payment_id_pago}...")
    
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
    reemitir_nf()
