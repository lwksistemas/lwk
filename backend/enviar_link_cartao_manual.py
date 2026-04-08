"""
Script para enviar link de cadastro de cartão manualmente
"""
import os
import django
import logging

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.sync_service import AsaasSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enviar_link_cartao(slug_loja):
    """Envia link de cadastro de cartão para uma loja"""
    
    try:
        # Buscar loja
        loja = Loja.objects.get(slug=slug_loja)
        logger.info(f"Loja encontrada: {loja.nome} ({loja.slug})")
        logger.info(f"Forma pagamento preferida: {loja.forma_pagamento_preferida}")
        
        # Buscar financeiro
        financeiro = FinanceiroLoja.objects.filter(loja=loja).first()
        if not financeiro:
            logger.error(f"Financeiro não encontrado para loja {slug_loja}")
            return
        
        logger.info(f"Financeiro encontrado: status={financeiro.status_pagamento}")
        
        # Enviar link
        sync_service = AsaasSyncService()
        sync_service._enviar_link_cadastro_cartao(loja, financeiro)
        
        logger.info("✅ Link de cadastro de cartão enviado com sucesso!")
        logger.info(f"Verifique o email: {loja.owner.email}")
        
    except Loja.DoesNotExist:
        logger.error(f"Loja {slug_loja} não encontrada")
    except Exception as e:
        logger.error(f"Erro ao enviar link: {e}", exc_info=True)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python enviar_link_cartao_manual.py <slug_loja>")
        print("Exemplo: python enviar_link_cartao_manual.py 22239255889")
        sys.exit(1)
    
    slug_loja = sys.argv[1]
    logger.info(f"Enviando link de cartão para loja: {slug_loja}")
    enviar_link_cartao(slug_loja)
