"""
Testes de validação central tenant (JWT → lojas permitidas → header/URL).
"""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from superadmin.models import Loja, PlanoAssinatura, TipoLoja, VendedorUsuario
from tenants.middleware import TenantMiddleware, ensure_loja_context
from core.tenant_access import user_can_access_loja, check_cross_tenant_access


class TenantAccessTestCase(TestCase):
    def setUp(self):
        self.tipo = TipoLoja.objects.create(
            nome='CRM Vendas',
            slug='crm-vendas',
            codigo='CRMVND',
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico',
            slug='basico',
            preco_mensal=99.90,
        )
        self.owner_a = User.objects.create_user(
            username='owner_a@test.com',
            email='owner_a@test.com',
            password='senha123',
        )
        self.owner_b = User.objects.create_user(
            username='owner_b@test.com',
            email='owner_b@test.com',
            password='senha123',
        )
        self.loja_a = Loja.objects.create(
            nome='Loja A',
            slug='loja-a',
            cpf_cnpj='11111111000111',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner_a,
            database_name='loja_a',
        )
        self.loja_b = Loja.objects.create(
            nome='Loja B',
            slug='loja-b',
            cpf_cnpj='22222222000222',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner_b,
            database_name='loja_b',
        )
        self.factory = RequestFactory()

    def test_owner_can_access_own_loja(self):
        self.assertTrue(user_can_access_loja(self.owner_a, self.loja_a))
        self.assertFalse(user_can_access_loja(self.owner_a, self.loja_b))

    def test_vendedor_can_access_linked_loja(self):
        vendedor_user = User.objects.create_user(
            username='vendedor@test.com',
            email='vendedor@test.com',
            password='senha123',
        )
        VendedorUsuario.objects.create(user=vendedor_user, loja=self.loja_a)
        self.assertTrue(user_can_access_loja(vendedor_user, self.loja_a))
        self.assertFalse(user_can_access_loja(vendedor_user, self.loja_b))

    def test_user_belongs_to_store_fail_closed_on_unknown_slug(self):
        from core.store_membership import user_belongs_to_store

        self.assertFalse(user_belongs_to_store(self.owner_a, 'slug-inexistente'))

    def test_check_cross_tenant_access_blocks_wrong_header(self):
        request = self.factory.get(
            '/api/crm-vendas/leads/',
            HTTP_X_TENANT_SLUG='loja-b',
        )
        request.user = self.owner_a
        response = check_cross_tenant_access(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)

    def test_middleware_blocks_cross_tenant_path(self):
        request = self.factory.get('/loja/loja-b/crm-vendas/leads/')
        request.user = self.owner_a
        middleware = TenantMiddleware(lambda r: None)
        response = middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_ensure_loja_context_denies_foreign_loja(self):
        request = self.factory.get(
            '/api/crm-vendas/leads/',
            HTTP_X_TENANT_SLUG='loja-b',
        )
        request.user = self.owner_a
        self.assertFalse(ensure_loja_context(request))
