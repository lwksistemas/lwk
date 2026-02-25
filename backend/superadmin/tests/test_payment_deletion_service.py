"""
Testes para o serviço unificado de exclusão de pagamentos
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from superadmin.payment_deletion_service import (
    UnifiedPaymentDeletionService,
    AsaasPaymentStrategy,
    MercadoPagoPaymentStrategy,
    PaymentProviderStrategy
)


class TestPaymentProviderStrategy(TestCase):
    """Testes para a interface abstrata PaymentProviderStrategy"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Não deve ser possível instanciar a classe abstrata diretamente"""
        with self.assertRaises(TypeError):
            PaymentProviderStrategy()


class TestAsaasPaymentStrategy(TestCase):
    """Testes para AsaasPaymentStrategy"""
    
    def setUp(self):
        self.strategy = AsaasPaymentStrategy()
    
    def test_provider_name(self):
        """Deve retornar o nome correto do provedor"""
        self.assertEqual(self.strategy.provider_name, "Asaas")
    
    @patch('superadmin.payment_deletion_service.AsaasDeletionService')
    def test_available_when_service_configured(self, mock_service):
        """Deve estar disponível quando o serviço está configurado"""
        mock_instance = Mock()
        mock_instance.available = True
        mock_service.return_value = mock_instance
        
        strategy = AsaasPaymentStrategy()
        self.assertTrue(strategy.available)
    
    @patch('superadmin.payment_deletion_service.AsaasDeletionService')
    def test_cancel_payments_success(self, mock_service):
        """Deve cancelar pagamentos com sucesso"""
        mock_instance = Mock()
        mock_instance.available = True
        mock_instance.delete_loja_from_asaas.return_value = {
            'success': True,
            'deleted_payments': 5,
            'deleted_customer': True
        }
        mock_service.return_value = mock_instance
        
        strategy = AsaasPaymentStrategy()
        result = strategy.cancel_payments('loja-teste')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['cancelled_count'], 5)
        self.assertTrue(result['deleted_customer'])
    
    @patch('superadmin.payment_deletion_service.AsaasDeletionService')
    def test_cancel_payments_when_unavailable(self, mock_service):
        """Deve retornar erro quando o serviço não está disponível"""
        mock_instance = Mock()
        mock_instance.available = False
        mock_service.return_value = mock_instance
        
        strategy = AsaasPaymentStrategy()
        result = strategy.cancel_payments('loja-teste')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['cancelled_count'], 0)
        self.assertIn('não configurado', result['error'])


class TestMercadoPagoPaymentStrategy(TestCase):
    """Testes para MercadoPagoPaymentStrategy"""
    
    def setUp(self):
        self.strategy = MercadoPagoPaymentStrategy()
    
    def test_provider_name(self):
        """Deve retornar o nome correto do provedor"""
        self.assertEqual(self.strategy.provider_name, "Mercado Pago")
    
    @patch('superadmin.payment_deletion_service.LojaMercadoPagoService')
    def test_available_when_service_configured(self, mock_service):
        """Deve estar disponível quando o serviço está configurado"""
        mock_instance = Mock()
        mock_instance.available = True
        mock_service.return_value = mock_instance
        
        strategy = MercadoPagoPaymentStrategy()
        self.assertTrue(strategy.available)
    
    @patch('superadmin.payment_deletion_service.LojaMercadoPagoService')
    def test_cancel_payments_success(self, mock_service):
        """Deve cancelar pagamentos com sucesso"""
        mock_instance = Mock()
        mock_instance.available = True
        mock_instance.cancel_pending_payments_loja.return_value = {
            'success': True,
            'cancelled_count': 3
        }
        mock_service.return_value = mock_instance
        
        strategy = MercadoPagoPaymentStrategy()
        result = strategy.cancel_payments('loja-teste')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['cancelled_count'], 3)


class TestUnifiedPaymentDeletionService(TestCase):
    """Testes para UnifiedPaymentDeletionService"""
    
    def setUp(self):
        self.service = UnifiedPaymentDeletionService()
    
    def test_has_multiple_providers(self):
        """Deve ter múltiplos provedores registrados"""
        self.assertGreaterEqual(len(self.service.providers), 2)
    
    def test_get_available_providers(self):
        """Deve retornar lista de provedores disponíveis"""
        providers = self.service.get_available_providers()
        
        self.assertIsInstance(providers, list)
        self.assertGreater(len(providers), 0)
        
        for provider in providers:
            self.assertIn('name', provider)
            self.assertIn('available', provider)
    
    @patch('superadmin.payment_deletion_service.AsaasPaymentStrategy')
    @patch('superadmin.payment_deletion_service.MercadoPagoPaymentStrategy')
    def test_delete_all_payments_success(self, mock_mp, mock_asaas):
        """Deve deletar pagamentos de todos os provedores com sucesso"""
        # Mock Asaas
        mock_asaas_instance = Mock()
        mock_asaas_instance.provider_name = "Asaas"
        mock_asaas_instance.available = True
        mock_asaas_instance.cancel_payments.return_value = {
            'success': True,
            'cancelled_count': 5,
            'deleted_customer': True
        }
        mock_asaas_instance.delete_local_data.return_value = {
            'success': True,
            'deleted_payments': 5,
            'deleted_customers': 1,
            'deleted_subscriptions': 1
        }
        mock_asaas.return_value = mock_asaas_instance
        
        # Mock Mercado Pago
        mock_mp_instance = Mock()
        mock_mp_instance.provider_name = "Mercado Pago"
        mock_mp_instance.available = True
        mock_mp_instance.cancel_payments.return_value = {
            'success': True,
            'cancelled_count': 3
        }
        mock_mp_instance.delete_local_data.return_value = {
            'success': True,
            'deleted_payments': 3,
            'deleted_customers': 0,
            'deleted_subscriptions': 0
        }
        mock_mp.return_value = mock_mp_instance
        
        # Criar serviço com mocks
        service = UnifiedPaymentDeletionService()
        service.providers = [mock_asaas_instance, mock_mp_instance]
        
        # Executar
        result = service.delete_all_payments_for_loja('loja-teste')
        
        # Verificar
        self.assertEqual(result['loja_slug'], 'loja-teste')
        self.assertEqual(result['total_cancelled'], 8)  # 5 + 3
        self.assertEqual(result['total_deleted_payments'], 8)  # 5 + 3
        self.assertEqual(result['total_deleted_customers'], 1)
        self.assertEqual(result['total_deleted_subscriptions'], 1)
        self.assertEqual(len(result['errors']), 0)
        
        # Verificar que ambos os provedores foram chamados
        mock_asaas_instance.cancel_payments.assert_called_once_with('loja-teste')
        mock_asaas_instance.delete_local_data.assert_called_once_with('loja-teste')
        mock_mp_instance.cancel_payments.assert_called_once_with('loja-teste')
        mock_mp_instance.delete_local_data.assert_called_once_with('loja-teste')
    
    @patch('superadmin.payment_deletion_service.AsaasPaymentStrategy')
    @patch('superadmin.payment_deletion_service.MercadoPagoPaymentStrategy')
    def test_delete_all_payments_with_unavailable_provider(self, mock_mp, mock_asaas):
        """Deve continuar mesmo se um provedor não estiver disponível"""
        # Mock Asaas (disponível)
        mock_asaas_instance = Mock()
        mock_asaas_instance.provider_name = "Asaas"
        mock_asaas_instance.available = True
        mock_asaas_instance.cancel_payments.return_value = {
            'success': True,
            'cancelled_count': 5
        }
        mock_asaas_instance.delete_local_data.return_value = {
            'success': True,
            'deleted_payments': 5,
            'deleted_customers': 1,
            'deleted_subscriptions': 1
        }
        mock_asaas.return_value = mock_asaas_instance
        
        # Mock Mercado Pago (indisponível)
        mock_mp_instance = Mock()
        mock_mp_instance.provider_name = "Mercado Pago"
        mock_mp_instance.available = False
        mock_mp.return_value = mock_mp_instance
        
        # Criar serviço com mocks
        service = UnifiedPaymentDeletionService()
        service.providers = [mock_asaas_instance, mock_mp_instance]
        
        # Executar
        result = service.delete_all_payments_for_loja('loja-teste')
        
        # Verificar
        self.assertEqual(result['total_cancelled'], 5)  # Apenas Asaas
        self.assertIn('Mercado Pago', result['providers'])
        self.assertFalse(result['providers']['Mercado Pago']['available'])
        
        # Verificar que apenas Asaas foi chamado
        mock_asaas_instance.cancel_payments.assert_called_once()
        mock_mp_instance.cancel_payments.assert_not_called()
    
    @patch('superadmin.payment_deletion_service.AsaasPaymentStrategy')
    def test_delete_all_payments_handles_exceptions(self, mock_asaas):
        """Deve capturar e registrar exceções sem interromper o processo"""
        # Mock Asaas que lança exceção
        mock_asaas_instance = Mock()
        mock_asaas_instance.provider_name = "Asaas"
        mock_asaas_instance.available = True
        mock_asaas_instance.cancel_payments.side_effect = Exception("Erro de teste")
        mock_asaas_instance.delete_local_data.return_value = {
            'success': True,
            'deleted_payments': 0,
            'deleted_customers': 0,
            'deleted_subscriptions': 0
        }
        mock_asaas.return_value = mock_asaas_instance
        
        # Criar serviço com mock
        service = UnifiedPaymentDeletionService()
        service.providers = [mock_asaas_instance]
        
        # Executar
        result = service.delete_all_payments_for_loja('loja-teste')
        
        # Verificar que o erro foi registrado
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Erro de teste', result['errors'][0])
        
        # Verificar que delete_local_data ainda foi chamado
        mock_asaas_instance.delete_local_data.assert_called_once()
