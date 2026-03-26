"""
Script para atualizar cliente no Asaas com CEP correto

Problema: CEP foi enviado como "14026-59" (incompleto)
Solução: Atualizar para "14026590" (8 dígitos)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja
from asaas_integration.client import AsaasClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def atualizar_cliente_asaas():
    """Atualiza cliente no Asaas com CEP correto"""
    
    # Buscar loja
    loja = Loja.objects.get(slug='41449198000172')
    fin = loja.financeiro
    
    logger.info(f"Loja: {loja.nome}")
    logger.info(f"Customer ID: {fin.asaas_customer_id}")
    logger.info(f"CEP no banco: {loja.cep}")
    
    # Limpar CEP (apenas dígitos)
    cep_limpo = ''.join(c for c in loja.cep if c.isdigit())
    logger.info(f"CEP limpo: {cep_limpo}")
    
    # Verificar se CEP tem 8 dígitos
    if len(cep_limpo) < 8:
        logger.error(f"CEP incompleto: {cep_limpo} (precisa de 8 dígitos)")
        logger.info("Por favor, corrija o CEP no banco de dados primeiro")
        return False
    
    # Criar cliente Asaas
    client = AsaasClient()
    
    # Atualizar cliente
    customer_data = {
        'name': loja.nome,
        'email': loja.owner.email,
        'cpfCnpj': loja.cpf_cnpj,
        'phone': loja.owner_telefone or '',
        'address': loja.logradouro or '',
        'addressNumber': loja.numero or '',
        'complement': loja.complemento or '',
        'province': loja.bairro or '',
        'city': loja.cidade or '',
        'state': loja.uf or '',
        'postalCode': cep_limpo,
    }
    
    logger.info("Atualizando cliente no Asaas...")
    logger.info(f"Dados: {customer_data}")
    
    try:
        result = client.update_customer(fin.asaas_customer_id, customer_data)
        logger.info(f"✅ Cliente atualizado com sucesso!")
        logger.info(f"Resultado: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar cliente: {e}")
        return False

if __name__ == '__main__':
    atualizar_cliente_asaas()
