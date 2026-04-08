"""
Script para reprocessar webhook de pagamento manualmente
Útil quando o webhook falhou e precisa ser reprocessado
"""
import os
import django
import logging

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.sync_service import AsaasSyncService
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocessar_pagamento(slug_loja):
    """Reprocessa webhook de pagamento para uma loja específica"""
    
    try:
        # Buscar loja
        loja = Loja.objects.get(slug=slug_loja)
        logger.info(f"Loja encontrada: {loja.nome} ({loja.slug})")
        
        # Buscar financeiro
        financeiro = FinanceiroLoja.objects.filter(loja=loja).first()
        if not financeiro:
            logger.error(f"Financeiro não encontrado para loja {slug_loja}")
            return
        
        logger.info(f"Financeiro encontrado: payment_id={financeiro.asaas_payment_id}, status={financeiro.status_pagamento}")
        
        # Buscar dados do pagamento no Asaas
        config = AsaasConfig.get_config()
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        payment_data = client.get_payment(financeiro.asaas_payment_id)
        logger.info(f"Dados do pagamento no Asaas: status={payment_data.get('status')}")
        
        # Reprocessar webhook
        sync_service = AsaasSyncService()
        
        # Simular webhook de pagamento recebido
        webhook_data = {
            'id': payment_data['id'],
            'event': 'PAYMENT_RECEIVED',
            'status': payment_data['status'],
            **payment_data
        }
        
        logger.info("Reprocessando webhook...")
        result = sync_service.process_webhook_payment(webhook_data)
        
        logger.info(f"Resultado: {result}")
        
        if result.get('success'):
            logger.info("✅ Webhook reprocessado com sucesso!")
            logger.info("Verifique o email para confirmar o recebimento dos emails:")
            logger.info(f"  - Email de senha de acesso")
            logger.info(f"  - Email com link para cadastrar cartão")
        else:
            logger.error(f"❌ Erro ao reprocessar webhook: {result.get('error')}")
        
    except Loja.DoesNotExist:
        logger.error(f"Loja {slug_loja} não encontrada")
    except Exception as e:
        logger.error(f"Erro ao reprocessar pagamento: {e}", exc_info=True)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python reprocessar_pagamento_webhook.py <slug_loja>")
        print("Exemplo: python reprocessar_pagamento_webhook.py 22239255889")
        sys.exit(1)
    
    slug_loja = sys.argv[1]
    logger.info(f"Reprocessando pagamento para loja: {slug_loja}")
    reprocessar_pagamento(slug_loja)
