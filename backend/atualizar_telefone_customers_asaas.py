"""
Script para atualizar telefone dos customers existentes no Asaas
Garante que todas as notas fiscais futuras incluam o telefone do administrador
"""
import os
import django
import logging

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def atualizar_telefone_customers():
    """Atualiza telefone de todos os customers no Asaas"""
    
    # Obter configuração do Asaas
    try:
        config = AsaasConfig.get_config()
        if not config.api_key or not config.enabled:
            logger.error("Asaas não configurado ou desabilitado")
            return
        
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        logger.info(f"Conectado ao Asaas ({'SANDBOX' if config.sandbox else 'PRODUÇÃO'})")
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração Asaas: {e}")
        return
    
    # Buscar todas as lojas com customer_id no Asaas
    financeiros = FinanceiroLoja.objects.filter(
        asaas_customer_id__isnull=False
    ).exclude(asaas_customer_id='').select_related('loja')
    
    total = financeiros.count()
    logger.info(f"Encontradas {total} lojas com customer no Asaas")
    
    atualizados = 0
    erros = 0
    sem_telefone = 0
    
    for financeiro in financeiros:
        loja = financeiro.loja
        customer_id = financeiro.asaas_customer_id
        
        # Verificar se a loja tem telefone
        telefone = (loja.owner_telefone or '').strip()
        
        if not telefone:
            logger.warning(f"Loja {loja.slug} não tem telefone cadastrado")
            sem_telefone += 1
            continue
        
        try:
            # Buscar customer atual no Asaas
            customer = client.get_customer(customer_id)
            telefone_atual = customer.get('phone', '')
            
            # Verificar se precisa atualizar
            if telefone_atual == telefone:
                logger.info(f"✓ Loja {loja.slug}: telefone já está correto ({telefone})")
                atualizados += 1
                continue
            
            # Atualizar customer com telefone
            logger.info(f"Atualizando loja {loja.slug}: {telefone_atual} → {telefone}")
            
            customer_data = {
                'phone': telefone
            }
            
            client.update_customer(customer_id, customer_data)
            logger.info(f"✓ Loja {loja.slug}: telefone atualizado com sucesso")
            atualizados += 1
            
        except Exception as e:
            logger.error(f"✗ Erro ao atualizar loja {loja.slug} (customer {customer_id}): {e}")
            erros += 1
    
    # Resumo
    logger.info("\n" + "="*60)
    logger.info("RESUMO DA ATUALIZAÇÃO")
    logger.info("="*60)
    logger.info(f"Total de lojas processadas: {total}")
    logger.info(f"Atualizadas com sucesso: {atualizados}")
    logger.info(f"Sem telefone cadastrado: {sem_telefone}")
    logger.info(f"Erros: {erros}")
    logger.info("="*60)
    
    if sem_telefone > 0:
        logger.warning(f"\n⚠️  {sem_telefone} lojas não têm telefone cadastrado!")
        logger.warning("Essas lojas precisam ter o telefone atualizado no cadastro.")

if __name__ == '__main__':
    logger.info("Iniciando atualização de telefones dos customers no Asaas...")
    atualizar_telefone_customers()
    logger.info("Atualização concluída!")
