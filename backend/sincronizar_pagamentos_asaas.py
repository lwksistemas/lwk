#!/usr/bin/env python
"""
Script para sincronizar pagamentos do Asaas que estão faltando no banco local
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.client import AsaasClient
from asaas_integration.models import AsaasPayment, AsaasCustomer
from superadmin.models import Loja
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sincronizar_pagamentos_faltantes():
    """Busca pagamentos no Asaas e sincroniza com banco local"""
    
    try:
        # Obter API key das variáveis de ambiente
        from decouple import config
        api_key = config('ASAAS_API_KEY', default='')
        sandbox = config('ASAAS_SANDBOX', default='True', cast=bool)
        
        if not api_key:
            logger.error("❌ ASAAS_API_KEY não configurada!")
            return
        
        # Inicializar cliente Asaas
        client = AsaasClient(api_key=api_key, sandbox=sandbox)
        
        logger.info("🔍 Buscando todos os pagamentos no Asaas...")
        
        # Buscar todos os pagamentos do Asaas
        response = client._make_request('GET', 'payments', {
            'limit': 100,
            'offset': 0
        })
        
        payments_asaas = response.get('data', [])
        logger.info(f"📊 Total de pagamentos no Asaas: {len(payments_asaas)}")
        
        # Buscar IDs dos pagamentos já existentes no banco
        existing_ids = set(AsaasPayment.objects.values_list('asaas_id', flat=True))
        logger.info(f"📊 Total de pagamentos no banco local: {len(existing_ids)}")
        
        # Filtrar pagamentos que não estão no banco
        missing_payments = [p for p in payments_asaas if p['id'] not in existing_ids]
        logger.info(f"⚠️  Pagamentos faltantes no banco: {len(missing_payments)}")
        
        if not missing_payments:
            logger.info("✅ Todos os pagamentos já estão sincronizados!")
            return
        
        # Sincronizar cada pagamento faltante
        sincronizados = 0
        for payment_data in missing_payments:
            try:
                logger.info(f"\n📝 Sincronizando pagamento: {payment_data['id']}")
                logger.info(f"   - Descrição: {payment_data.get('description', 'N/A')}")
                logger.info(f"   - Valor: R$ {payment_data.get('value', 0)}")
                logger.info(f"   - Vencimento: {payment_data.get('dueDate', 'N/A')}")
                logger.info(f"   - Status: {payment_data.get('status', 'N/A')}")
                
                # Buscar ou criar customer
                customer_id = payment_data.get('customer')
                if not customer_id:
                    logger.warning(f"   ⚠️  Pagamento sem customer, pulando...")
                    continue
                
                # Buscar dados do customer no Asaas
                try:
                    customer_data = client.get_customer(customer_id)
                except Exception as e:
                    logger.error(f"   ❌ Erro ao buscar customer {customer_id}: {e}")
                    continue
                
                # Criar ou buscar customer no banco
                customer, created = AsaasCustomer.objects.get_or_create(
                    asaas_id=customer_id,
                    defaults={
                        'name': customer_data.get('name', ''),
                        'email': customer_data.get('email', ''),
                        'cpf_cnpj': customer_data.get('cpfCnpj', ''),
                        'phone': customer_data.get('phone', ''),
                    }
                )
                
                if created:
                    logger.info(f"   ✅ Customer criado: {customer.name}")
                else:
                    logger.info(f"   ℹ️  Customer já existe: {customer.name}")
                
                # Buscar dados do PIX (se disponível)
                pix_copy_paste = ''
                try:
                    pix_data = client.get_pix_qr_code(payment_data['id'])
                    pix_copy_paste = pix_data.get('payload', '')
                except:
                    pass
                
                # Criar pagamento no banco
                payment = AsaasPayment.objects.create(
                    customer=customer,
                    asaas_id=payment_data['id'],
                    value=payment_data.get('value', 0),
                    status=payment_data.get('status', 'PENDING'),
                    due_date=payment_data.get('dueDate'),
                    payment_date=payment_data.get('paymentDate'),
                    description=payment_data.get('description', ''),
                    bank_slip_url=payment_data.get('bankSlipUrl', ''),
                    pix_copy_paste=pix_copy_paste,
                    external_reference=payment_data.get('externalReference', '')
                )
                
                logger.info(f"   ✅ Pagamento sincronizado (ID local: {payment.id})")
                sincronizados += 1
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao sincronizar pagamento {payment_data['id']}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"\n🎉 Sincronização concluída!")
        logger.info(f"   - Total de pagamentos sincronizados: {sincronizados}")
        logger.info(f"   - Total de pagamentos no banco agora: {AsaasPayment.objects.count()}")
        
    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("SINCRONIZAÇÃO DE PAGAMENTOS ASAAS")
    logger.info("=" * 60)
    sincronizar_pagamentos_faltantes()
    logger.info("=" * 60)
