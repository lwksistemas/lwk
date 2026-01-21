"""
Serviço para exclusão de dados no Asaas
Remove clientes, pagamentos e boletos da API do Asaas
"""
import logging
from typing import Dict, List, Any
from .client import AsaasClient
from .models import AsaasConfig, AsaasCustomer, AsaasPayment, LojaAssinatura

logger = logging.getLogger(__name__)

class AsaasDeletionService:
    """Serviço para exclusão de dados no Asaas"""
    
    def __init__(self):
        try:
            config = AsaasConfig.get_config()
            if config.api_key and config.enabled:
                self.client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
                self.available = True
            else:
                self.client = None
                self.available = False
                logger.warning("Asaas não configurado ou desabilitado")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço de exclusão Asaas: {e}")
            self.client = None
            self.available = False
    
    def delete_loja_from_asaas(self, loja_slug: str) -> Dict[str, Any]:
        """
        Exclui todos os dados de uma loja no Asaas
        
        Args:
            loja_slug: Slug da loja a ser excluída
            
        Returns:
            Dict com resultado da operação
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Serviço Asaas não disponível'
            }
        
        try:
            logger.info(f"🗑️ Iniciando exclusão Asaas para loja: {loja_slug}")
            
            # Buscar assinatura da loja
            try:
                assinatura = LojaAssinatura.objects.get(loja_slug=loja_slug)
            except LojaAssinatura.DoesNotExist:
                logger.info(f"ℹ️ Nenhuma assinatura Asaas encontrada para loja: {loja_slug}")
                return {
                    'success': True,
                    'message': 'Nenhuma assinatura Asaas encontrada',
                    'deleted_payments': 0,
                    'deleted_customers': 0
                }
            
            customer = assinatura.asaas_customer
            customer_id = customer.asaas_id
            
            # 1. Buscar e cancelar todos os pagamentos do cliente
            deleted_payments = self._delete_customer_payments(customer_id)
            
            # 2. Excluir cliente no Asaas
            deleted_customer = self._delete_customer_from_asaas(customer_id)
            
            # 3. Limpar dados locais (será feito pelos signals)
            
            logger.info(f"✅ Exclusão Asaas concluída para loja: {loja_slug}")
            
            return {
                'success': True,
                'loja_slug': loja_slug,
                'customer_id': customer_id,
                'deleted_payments': deleted_payments,
                'deleted_customer': deleted_customer,
                'message': f'Dados Asaas excluídos: {deleted_payments} pagamentos, 1 cliente'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao excluir dados Asaas da loja {loja_slug}: {e}")
            return {
                'success': False,
                'error': str(e),
                'loja_slug': loja_slug
            }
    
    def _delete_customer_payments(self, customer_id: str) -> int:
        """Cancela todos os pagamentos de um cliente"""
        try:
            deleted_count = 0
            
            # Buscar pagamentos do cliente na API
            try:
                payments_response = self.client.list_customer_payments(customer_id)
                payments = payments_response.get('data', [])
                
                logger.info(f"📋 Encontrados {len(payments)} pagamentos para cliente {customer_id}")
                
                for payment in payments:
                    payment_id = payment.get('id')
                    payment_status = payment.get('status')
                    
                    # Só cancelar pagamentos que podem ser cancelados
                    if payment_status in ['PENDING', 'AWAITING_PAYMENT', 'OVERDUE']:
                        try:
                            self.client.delete_payment(payment_id)
                            deleted_count += 1
                            logger.info(f"✅ Pagamento cancelado: {payment_id}")
                        except Exception as e:
                            # Verificar se é erro de status inválido
                            if "não pode ser removida" in str(e) or "invalid_action" in str(e):
                                logger.info(f"ℹ️ Pagamento {payment_id} não pode ser cancelado (já processado)")
                            else:
                                logger.warning(f"⚠️ Erro ao cancelar pagamento {payment_id}: {e}")
                    else:
                        logger.info(f"ℹ️ Pagamento {payment_id} não cancelado (status: {payment_status})")
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao buscar pagamentos do cliente {customer_id}: {e}")
            
            # Também tentar cancelar pagamentos do banco local
            try:
                local_payments = AsaasPayment.objects.filter(customer__asaas_id=customer_id)
                
                for payment in local_payments:
                    if payment.status in ['PENDING', 'AWAITING_PAYMENT', 'OVERDUE']:
                        try:
                            self.client.delete_payment(payment.asaas_id)
                            deleted_count += 1
                            logger.info(f"✅ Pagamento local cancelado: {payment.asaas_id}")
                        except Exception as e:
                            # Verificar se é erro de status inválido
                            if "não pode ser removida" in str(e) or "invalid_action" in str(e):
                                logger.info(f"ℹ️ Pagamento local {payment.asaas_id} não pode ser cancelado (já processado)")
                            else:
                                logger.warning(f"⚠️ Erro ao cancelar pagamento local {payment.asaas_id}: {e}")
                    else:
                        logger.info(f"ℹ️ Pagamento local {payment.asaas_id} não cancelado (status: {payment.status})")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar pagamentos locais: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erro ao excluir pagamentos do cliente {customer_id}: {e}")
            return 0
    
    def _delete_customer_from_asaas(self, customer_id: str) -> bool:
        """Exclui cliente da API do Asaas"""
        try:
            self.client.delete_customer(customer_id)
            logger.info(f"✅ Cliente excluído do Asaas: {customer_id}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao excluir cliente {customer_id} do Asaas: {e}")
            # Alguns clientes podem não poder ser excluídos se tiverem histórico
            return False
    
    def cleanup_orphaned_asaas_data(self) -> Dict[str, Any]:
        """Limpa dados Asaas órfãos (sem loja correspondente)"""
        if not self.available:
            return {
                'success': False,
                'error': 'Serviço Asaas não disponível'
            }
        
        try:
            logger.info("🧹 Iniciando limpeza de dados Asaas órfãos")
            
            cleaned_customers = 0
            cleaned_payments = 0
            
            # Buscar assinaturas sem loja correspondente
            from superadmin.models import Loja
            
            orphaned_subscriptions = []
            for subscription in LojaAssinatura.objects.all():
                try:
                    Loja.objects.get(slug=subscription.loja_slug, is_active=True)
                except Loja.DoesNotExist:
                    orphaned_subscriptions.append(subscription)
            
            logger.info(f"📋 Encontradas {len(orphaned_subscriptions)} assinaturas órfãs")
            
            for subscription in orphaned_subscriptions:
                try:
                    # Excluir dados do Asaas
                    result = self.delete_loja_from_asaas(subscription.loja_slug)
                    if result.get('success'):
                        cleaned_customers += result.get('deleted_customer', 0)
                        cleaned_payments += result.get('deleted_payments', 0)
                    
                    # Excluir dados locais
                    subscription.delete()
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao limpar assinatura órfã {subscription.loja_slug}: {e}")
            
            return {
                'success': True,
                'cleaned_customers': cleaned_customers,
                'cleaned_payments': cleaned_payments,
                'cleaned_subscriptions': len(orphaned_subscriptions)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de dados órfãos: {e}")
            return {
                'success': False,
                'error': str(e)
            }