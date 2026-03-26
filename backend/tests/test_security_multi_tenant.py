"""
Testes de Segurança Multi-Tenant

Valida isolamento de dados entre lojas e previne acesso cross-tenant.
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from superadmin.models import Loja, TipoLoja, PlanoAssinatura, VendedorUsuario
from crm_vendas.models import Lead, Vendedor, Conta
from tenants.middleware import TenantMiddleware, set_current_tenant_db


class MultiTenantSecurityTestCase(TestCase):
    """Testes de segurança para isolamento multi-tenant."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        # Criar tipo e plano
        self.tipo_loja = TipoLoja.objects.create(
            nome='CRM Vendas',
            slug='crm-vendas',
            codigo='CRMVND'
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico',
            slug='basico',
            preco_mensal=99.90
        )
        
        # Criar loja A
        self.owner_a = User.objects.create_user(
            username='owner_a@test.com',
            email='owner_a@test.com',
            password='senha123'
        )
        self.loja_a = Loja.objects.create(
            nome='Loja A',
            slug='loja-a',
            cpf_cnpj='11111111000111',
            tipo_loja=self.tipo_loja,
            plano=self.plano,
            owner=self.owner_a,
            database_name='loja_a'
        )
        
        # Criar loja B
        self.owner_b = User.objects.create_user(
            username='owner_b@test.com',
            email='owner_b@test.com',
            password='senha123'
        )
        self.loja_b = Loja.objects.create(
            nome='Loja B',
            slug='loja-b',
            cpf_cnpj='22222222000222',
            tipo_loja=self.tipo_loja,
            plano=self.plano,
            owner=self.owner_b,
            database_name='loja_b'
        )
        
        self.factory = RequestFactory()
        self.client = APIClient()
    
    def get_token_for_user(self, user):
        """Gera token JWT para usuário."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_middleware_blocks_cross_tenant_access(self):
        """Testa se middleware bloqueia acesso cross-tenant."""
        # Owner da loja A tenta acessar loja B
        request = self.factory.get('/loja/loja-b/crm-vendas/leads/')
        request.user = self.owner_a
        
        middleware = TenantMiddleware(lambda r: None)
        response = middleware(request)
        
        # Deve retornar 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_loja_isolation_manager_filters_by_loja_id(self):
        """Testa se LojaIsolationManager filtra por loja_id."""
        # Criar vendedor na loja A
        set_current_tenant_db('loja_a')
        vendedor_a = Vendedor.objects.create(
            nome='Vendedor A',
            loja_id=self.loja_a.id
        )
        
        # Criar vendedor na loja B
        set_current_tenant_db('loja_b')
        vendedor_b = Vendedor.objects.create(
            nome='Vendedor B',
            loja_id=self.loja_b.id
        )
        
        # Buscar vendedores da loja A
        set_current_tenant_db('loja_a')
        vendedores_a = Vendedor.objects.all()
        
        # Deve retornar apenas vendedor A
        self.assertEqual(vendedores_a.count(), 1)
        self.assertEqual(vendedores_a.first().id, vendedor_a.id)
        
        # Buscar vendedores da loja B
        set_current_tenant_db('loja_b')
        vendedores_b = Vendedor.objects.all()
        
        # Deve retornar apenas vendedor B
        self.assertEqual(vendedores_b.count(), 1)
        self.assertEqual(vendedores_b.first().id, vendedor_b.id)
    
    def test_api_endpoint_respects_tenant_isolation(self):
        """Testa se endpoints da API respeitam isolamento."""
        # Criar lead na loja A
        set_current_tenant_db('loja_a')
        lead_a = Lead.objects.create(
            nome='Lead A',
            loja_id=self.loja_a.id
        )
        
        # Criar lead na loja B
        set_current_tenant_db('loja_b')
        lead_b = Lead.objects.create(
            nome='Lead B',
            loja_id=self.loja_b.id
        )
        
        # Owner A tenta listar leads
        token_a = self.get_token_for_user(self.owner_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_a}')
        
        response = self.client.get(f'/api/loja/{self.loja_a.slug}/crm-vendas/leads/')
        
        # Deve retornar apenas lead A
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Lead A')
    
    def test_cannot_create_resource_with_different_loja_id(self):
        """Testa se não é possível criar recurso com loja_id diferente."""
        token_a = self.get_token_for_user(self.owner_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_a}')
        
        # Tentar criar lead com loja_id da loja B
        response = self.client.post(
            f'/api/loja/{self.loja_a.slug}/crm-vendas/leads/',
            {
                'nome': 'Lead Malicioso',
                'loja_id': self.loja_b.id,  # Tentativa de injeção
                'email': 'test@test.com'
            }
        )
        
        # Deve criar com loja_id correto (loja A)
        if response.status_code == 201:
            lead = Lead.objects.get(id=response.data['id'])
            self.assertEqual(lead.loja_id, self.loja_a.id)
    
    def test_database_router_prevents_cross_database_queries(self):
        """Testa se database router previne queries cross-database."""
        set_current_tenant_db('loja_a')
        
        # Criar conta na loja A
        conta_a = Conta.objects.create(
            nome='Conta A',
            loja_id=self.loja_a.id
        )
        
        # Tentar buscar conta da loja B (não deve encontrar)
        set_current_tenant_db('loja_b')
        contas_b = Conta.objects.filter(id=conta_a.id)
        
        # Não deve encontrar (schemas isolados)
        self.assertEqual(contas_b.count(), 0)


class SecurityViolationTestCase(TestCase):
    """Testes para detecção de violações de segurança."""
    
    def test_detect_brute_force_attempt(self):
        """Testa detecção de tentativa de brute force."""
        # TODO: Implementar quando sistema de detecção estiver pronto
        pass
    
    def test_detect_rate_limit_exceeded(self):
        """Testa detecção de rate limit excedido."""
        # TODO: Implementar quando rate limiting estiver pronto
        pass
    
    def test_detect_suspicious_ip_change(self):
        """Testa detecção de mudança suspeita de IP."""
        # TODO: Implementar quando monitoramento de IP estiver pronto
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
