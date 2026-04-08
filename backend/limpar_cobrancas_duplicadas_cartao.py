"""
Script para limpar cobranças duplicadas de cadastro de cartão
Remove cobranças pendentes de R$ 5,00 que foram criadas durante testes
"""
import os
import django
import logging

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasConfig
from superadmin.models import Loja

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limpar_cobrancas_duplicadas(slug_loja):
    """Remove cobranças duplicadas de cadastro de cartão"""
    
    try:
        # Buscar loja
        loja = Loja.objects.get(slug=slug_loja)
        logger.info(f"Loja encontrada: {loja.nome} ({loja.slug})")
        
        # Buscar financeiro
        financeiro = loja.financeiro
        if not financeiro or not financeiro.asaas_customer_id:
            logger.error(f"Financeiro ou customer_id não encontrado para loja {slug_loja}")
            return
        
        logger.info(f"Customer ID: {financeiro.asaas_customer_id}")
        
        # Obter configuração do Asaas
        config = AsaasConfig.get_config()
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        # Buscar todas as cobranças do cliente
        logger.info("Buscando cobranças do cliente...")
        response = client._make_request('GET', f'payments?customer={financeiro.asaas_customer_id}')
        
        if not response.get('data'):
            logger.info("Nenhuma cobrança encontrada")
            return
        
        # Filtrar cobranças de R$ 5,00 de cadastro de cartão
        cobrancas_cartao_todas = [
            p for p in response.get('data', [])
            if p.get('value') == 5.0 
            and p.get('billingType') == 'CREDIT_CARD'
            and 'Cadastro de cartão' in p.get('description', '')
        ]
        
        logger.info(f"Encontradas {len(cobrancas_cartao_todas)} cobranças de cadastro de cartão")
        
        # Separar confirmadas e pendentes
        cobrancas_confirmadas = [p for p in cobrancas_cartao_todas if p.get('status') in ['CONFIRMED', 'RECEIVED']]
        cobrancas_pendentes = [p for p in cobrancas_cartao_todas if p.get('status') == 'PENDING']
        
        logger.info(f"  - {len(cobrancas_confirmadas)} confirmadas")
        logger.info(f"  - {len(cobrancas_pendentes)} pendentes")
        
        cobrancas_remover = []
        cobranca_manter = None
        
        # Se já existe uma confirmada, remover todas as pendentes
        if cobrancas_confirmadas:
            logger.info("Já existe cobrança confirmada, removendo todas as pendentes...")
            cobrancas_remover = cobrancas_pendentes
            cobranca_manter = cobrancas_confirmadas[0]
        # Se não tem confirmada, manter apenas a mais recente pendente
        elif len(cobrancas_pendentes) > 1:
            logger.info("Mantendo apenas a cobrança pendente mais recente...")
            cobrancas_pendentes.sort(key=lambda x: x.get('dateCreated'), reverse=True)
            cobranca_manter = cobrancas_pendentes[0]
            cobrancas_remover = cobrancas_pendentes[1:]
        else:
            logger.info("Não há cobranças duplicadas para remover")
            return
        
        if not cobrancas_remover:
            logger.info("Não há cobranças para remover")
            return
        
        logger.info(f"Mantendo cobrança: {cobranca_manter.get('id')} (status: {cobranca_manter.get('status')}, criada em {cobranca_manter.get('dateCreated')})")
        logger.info(f"Removendo {len(cobrancas_remover)} cobranças duplicadas...")
        
        for cobranca in cobrancas_remover:
            payment_id = cobranca.get('id')
            try:
                client._make_request('DELETE', f'payments/{payment_id}')
                logger.info(f"✅ Cobrança {payment_id} removida com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao remover cobrança {payment_id}: {e}")
        
        logger.info("✅ Limpeza concluída!")
        
        # Atualizar link no financeiro com a cobrança mantida
        payment_data = client._make_request('GET', f'payments/{cobranca_manter.get("id")}')
        if payment_data.get('invoiceUrl'):
            financeiro.link_pagamento_cartao = payment_data.get('invoiceUrl')
            financeiro.save()
            logger.info(f"Link de pagamento atualizado: {financeiro.link_pagamento_cartao}")
        
    except Loja.DoesNotExist:
        logger.error(f"Loja {slug_loja} não encontrada")
    except Exception as e:
        logger.error(f"Erro ao limpar cobranças: {e}", exc_info=True)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python limpar_cobrancas_duplicadas_cartao.py <slug_loja>")
        print("Exemplo: python limpar_cobrancas_duplicadas_cartao.py 22239255889")
        sys.exit(1)
    
    slug_loja = sys.argv[1]
    logger.info(f"Limpando cobranças duplicadas para loja: {slug_loja}")
    limpar_cobrancas_duplicadas(slug_loja)
