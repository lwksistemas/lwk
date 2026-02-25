"""
Serviço unificado para exclusão de pagamentos (Asaas e Mercado Pago)
Segue o padrão Strategy para permitir múltiplos provedores de pagamento
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.db import transaction

logger = logging.getLogger(__name__)


class PaymentProviderStrategy(ABC):
    """Interface abstrata para provedores de pagamento"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nome do provedor (ex: 'Asaas', 'Mercado Pago')"""
        pass
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Verifica se o provedor está configurado e disponível"""
        pass
    
    @abstractmethod
    def cancel_payments(self, loja_slug: str) -> Dict[str, Any]:
        """
        Cancela pagamentos pendentes na API do provedor
        
        Returns:
            Dict com: success, cancelled_count, error (opcional)
        """
        pass
    
    @abstractmethod
    def delete_local_data(self, loja_slug: str) -> Dict[str, Any]:
        """
        Remove dados locais do provedor (banco de dados)
        
        Returns:
            Dict com: success, deleted_payments, deleted_customers, deleted_subscriptions
        """
        pass


class AsaasPaymentStrategy(PaymentProviderStrategy):
    """Estratégia de exclusão para Asaas"""
    
    def __init__(self):
        self._deletion_service = None
        try:
            from asaas_integration.deletion_service import AsaasDeletionService
            self._deletion_service = AsaasDeletionService()
        except Exception as e:
            logger.warning(f"Erro ao inicializar AsaasDeletionService: {e}")
    
    @property
    def provider_name(self) -> str:
        return "Asaas"
    
    @property
    def available(self) -> bool:
        return self._deletion_service is not None and self._deletion_service.available
    
    def cancel_payments(self, loja_slug: str) -> Dict[str, Any]:
        """Cancela pagamentos na API do Asaas"""
        if not self.available:
            return {
                'success': False,
                'cancelled_count': 0,
                'error': f'{self.provider_name} não configurado ou desabilitado'
            }
        
        try:
            result = self._deletion_service.delete_loja_from_asaas(loja_slug)
            return {
                'success': result.get('success', False),
                'cancelled_count': result.get('deleted_payments', 0),
                'deleted_customer': result.get('deleted_customer', False),
                'error': result.get('error')
            }
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar pagamentos {self.provider_name}: {e}")
            return {
                'success': False,
                'cancelled_count': 0,
                'error': str(e)
            }
    
    def delete_local_data(self, loja_slug: str) -> Dict[str, Any]:
        """Remove dados locais do Asaas"""
        try:
            from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
            
            deleted_payments = 0
            deleted_customers = 0
            deleted_subscriptions = 0
            
            with transaction.atomic():
                try:
                    assinatura = LojaAssinatura.objects.get(loja_slug=loja_slug)
                    customer = assinatura.asaas_customer
                    
                    # Contar e deletar pagamentos
                    payments = AsaasPayment.objects.filter(customer=customer)
                    deleted_payments = payments.count()
                    payments.delete()
                    
                    # Deletar assinatura
                    assinatura.delete()
                    deleted_subscriptions = 1
                    
                    # Deletar cliente
                    customer.delete()
                    deleted_customers = 1
                    
                    logger.info(f"✅ Dados locais {self.provider_name} removidos: {deleted_payments} pagamentos, {deleted_customers} clientes, {deleted_subscriptions} assinaturas")
                    
                except LojaAssinatura.DoesNotExist:
                    logger.info(f"ℹ️ Nenhuma assinatura {self.provider_name} encontrada para loja: {loja_slug}")
            
            return {
                'success': True,
                'deleted_payments': deleted_payments,
                'deleted_customers': deleted_customers,
                'deleted_subscriptions': deleted_subscriptions
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover dados locais {self.provider_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_payments': 0,
                'deleted_customers': 0,
                'deleted_subscriptions': 0
            }


class MercadoPagoPaymentStrategy(PaymentProviderStrategy):
    """Estratégia de exclusão para Mercado Pago"""
    
    def __init__(self):
        self._service = None
        try:
            from superadmin.mercadopago_service import LojaMercadoPagoService
            self._service = LojaMercadoPagoService()
        except Exception as e:
            logger.warning(f"Erro ao inicializar LojaMercadoPagoService: {e}")
    
    @property
    def provider_name(self) -> str:
        return "Mercado Pago"
    
    @property
    def available(self) -> bool:
        return self._service is not None and self._service.available
    
    def cancel_payments(self, loja_slug: str) -> Dict[str, Any]:
        """Cancela pagamentos na API do Mercado Pago"""
        if not self.available:
            return {
                'success': False,
                'cancelled_count': 0,
                'error': f'{self.provider_name} não configurado ou desabilitado'
            }
        
        try:
            result = self._service.cancel_pending_payments_loja(loja_slug)
            return {
                'success': result.get('success', False),
                'cancelled_count': result.get('cancelled_count', 0),
                'error': result.get('error')
            }
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar pagamentos {self.provider_name}: {e}")
            return {
                'success': False,
                'cancelled_count': 0,
                'error': str(e)
            }
    
    def delete_local_data(self, loja_slug: str) -> Dict[str, Any]:
        """
        Remove dados locais do Mercado Pago
        
        NOTA: Mercado Pago não tem tabelas locais específicas como Asaas.
        Os payment_ids são armazenados em FinanceiroLoja e PagamentoLoja.
        A limpeza é feita automaticamente quando a loja é excluída (CASCADE).
        """
        try:
            from superadmin.models import FinanceiroLoja, PagamentoLoja, Loja
            
            deleted_payments = 0
            
            try:
                loja = Loja.objects.get(slug=loja_slug)
                
                # Contar pagamentos que serão removidos pelo CASCADE
                deleted_payments += FinanceiroLoja.objects.filter(
                    loja=loja
                ).exclude(mercadopago_payment_id='').count()
                
                deleted_payments += PagamentoLoja.objects.filter(
                    loja=loja
                ).exclude(mercadopago_payment_id='').count()
                
                logger.info(f"ℹ️ {deleted_payments} referências {self.provider_name} serão removidas pelo CASCADE")
                
            except Loja.DoesNotExist:
                logger.info(f"ℹ️ Loja não encontrada: {loja_slug}")
            
            return {
                'success': True,
                'deleted_payments': deleted_payments,
                'deleted_customers': 0,  # MP não tem tabela de clientes local
                'deleted_subscriptions': 0  # MP não tem tabela de assinaturas local
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar dados locais {self.provider_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_payments': 0,
                'deleted_customers': 0,
                'deleted_subscriptions': 0
            }


class UnifiedPaymentDeletionService:
    """
    Serviço unificado para exclusão de pagamentos de múltiplos provedores
    Usa o padrão Strategy para suportar diferentes provedores
    """
    
    def __init__(self):
        # Registrar todos os provedores disponíveis
        self.providers = [
            AsaasPaymentStrategy(),
            MercadoPagoPaymentStrategy(),
        ]
    
    def delete_all_payments_for_loja(self, loja_slug: str) -> Dict[str, Any]:
        """
        Cancela pagamentos e remove dados locais de TODOS os provedores
        
        Args:
            loja_slug: Slug da loja
            
        Returns:
            Dict com resultados agregados de todos os provedores
        """
        logger.info(f"🗑️ Iniciando exclusão de pagamentos para loja: {loja_slug}")
        
        results = {
            'loja_slug': loja_slug,
            'providers': {},
            'total_cancelled': 0,
            'total_deleted_payments': 0,
            'total_deleted_customers': 0,
            'total_deleted_subscriptions': 0,
            'errors': []
        }
        
        for provider in self.providers:
            provider_name = provider.provider_name
            logger.info(f"📋 Processando provedor: {provider_name}")
            
            provider_result = {
                'available': provider.available,
                'api_cancelled': 0,
                'local_deleted_payments': 0,
                'local_deleted_customers': 0,
                'local_deleted_subscriptions': 0,
                'errors': []
            }
            
            if not provider.available:
                logger.info(f"ℹ️ {provider_name} não configurado ou desabilitado")
                provider_result['errors'].append(f'{provider_name} não disponível')
                results['providers'][provider_name] = provider_result
                continue
            
            # 1. Cancelar pagamentos na API
            try:
                api_result = provider.cancel_payments(loja_slug)
                if api_result.get('success'):
                    cancelled = api_result.get('cancelled_count', 0)
                    provider_result['api_cancelled'] = cancelled
                    results['total_cancelled'] += cancelled
                    if cancelled > 0:
                        logger.info(f"✅ {provider_name}: {cancelled} pagamento(s) cancelado(s) na API")
                else:
                    error = api_result.get('error', 'Erro desconhecido')
                    provider_result['errors'].append(f'API: {error}')
                    logger.warning(f"⚠️ {provider_name} API: {error}")
            except Exception as e:
                error_msg = f'Erro ao cancelar na API: {str(e)}'
                provider_result['errors'].append(error_msg)
                results['errors'].append(f'{provider_name}: {error_msg}')
                logger.error(f"❌ {provider_name}: {error_msg}")
            
            # 2. Remover dados locais
            try:
                local_result = provider.delete_local_data(loja_slug)
                if local_result.get('success'):
                    provider_result['local_deleted_payments'] = local_result.get('deleted_payments', 0)
                    provider_result['local_deleted_customers'] = local_result.get('deleted_customers', 0)
                    provider_result['local_deleted_subscriptions'] = local_result.get('deleted_subscriptions', 0)
                    
                    results['total_deleted_payments'] += provider_result['local_deleted_payments']
                    results['total_deleted_customers'] += provider_result['local_deleted_customers']
                    results['total_deleted_subscriptions'] += provider_result['local_deleted_subscriptions']
                    
                    if provider_result['local_deleted_payments'] > 0:
                        logger.info(f"✅ {provider_name}: dados locais removidos")
                else:
                    error = local_result.get('error', 'Erro desconhecido')
                    provider_result['errors'].append(f'Local: {error}')
                    logger.warning(f"⚠️ {provider_name} local: {error}")
            except Exception as e:
                error_msg = f'Erro ao remover dados locais: {str(e)}'
                provider_result['errors'].append(error_msg)
                results['errors'].append(f'{provider_name}: {error_msg}')
                logger.error(f"❌ {provider_name}: {error_msg}")
            
            results['providers'][provider_name] = provider_result
        
        # Resumo final
        logger.info(f"✅ Exclusão de pagamentos concluída para loja: {loja_slug}")
        logger.info(f"   📊 Total: {results['total_cancelled']} cancelados na API, "
                   f"{results['total_deleted_payments']} pagamentos locais, "
                   f"{results['total_deleted_customers']} clientes, "
                   f"{results['total_deleted_subscriptions']} assinaturas")
        
        if results['errors']:
            logger.warning(f"   ⚠️ {len(results['errors'])} erro(s) encontrado(s)")
        
        return results
    
    def get_available_providers(self) -> list:
        """Retorna lista de provedores disponíveis"""
        return [
            {
                'name': provider.provider_name,
                'available': provider.available
            }
            for provider in self.providers
        ]
