"""
Testes de isolamento multi-tenant CRM — API e permissões (sem depender de schema tenant Postgres).

O SQLite de CI não materializa tabelas crm_vendas no default (MultiTenantRouter); estes testes
validam bloqueio cross-loja na camada de acesso e o comportamento do VendedorFilterMixin.
"""
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import RequestFactory, SimpleTestCase, TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from superadmin.authentication import invalidate_session_cache
from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from superadmin.session_manager import SessionManager
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class CrmTenantApiAccessTest(TestCase):
    """Owner da loja A não acessa API CRM com headers da loja B."""

    databases = {'default'}

    def setUp(self):
        uid = uuid.uuid4().hex[:10]
        self.tipo = TipoLoja.objects.create(
            nome='E-commerce',
            slug=f'tipo-tenant-{uid}',
            codigo=f'T{uid[:3]}',
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Tenant CRM',
            slug=f'plano-tenant-{uid}',
            preco_mensal=99,
        )
        self.owner_a = User.objects.create_user(
            username=f'owner-a-{uid}@test.com',
            email=f'owner-a-{uid}@test.com',
            password='pass12345',
        )
        self.owner_b = User.objects.create_user(
            username=f'owner-b-{uid}@test.com',
            email=f'owner-b-{uid}@test.com',
            password='pass12345',
        )
        self.loja_a = Loja.objects.create(
            nome='CRM Tenant A',
            slug=f'crm-tenant-a-{uid}',
            cpf_cnpj=f'33333333{uid[:6]}',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner_a,
            database_created=True,
        )
        self.loja_b = Loja.objects.create(
            nome='CRM Tenant B',
            slug=f'crm-tenant-b-{uid}',
            cpf_cnpj=f'44444444{uid[:6]}',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner_b,
            database_created=True,
        )
        invalidate_session_cache(self.owner_a.id)
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.owner_a).access_token)
        sid = SessionManager.create_session(self.owner_a.id, token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SESSION_ID=sid,
        )

    def tearDown(self):
        set_current_tenant_db('default')
        set_current_loja_id(None)

    def test_owner_a_bloqueado_com_headers_loja_b(self):
        response = self.client.get(
            '/api/crm-vendas/leads/',
            HTTP_X_LOJA_ID=str(self.loja_b.id),
            HTTP_X_TENANT_SLUG=self.loja_b.slug,
        )
        self.assertEqual(response.status_code, 403, response.content)

    @patch('crm_vendas.views_cadastros.LeadViewSet.list')
    def test_owner_a_permitido_com_headers_loja_a(self, mock_list):
        from rest_framework.response import Response

        mock_list.return_value = Response({'results': []})
        response = self.client.get(
            '/api/crm-vendas/leads/',
            HTTP_X_LOJA_ID=str(self.loja_a.id),
            HTTP_X_TENANT_SLUG=self.loja_a.slug,
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_ensure_loja_context_nega_loja_alheia(self):
        from tenants.middleware import ensure_loja_context

        factory = RequestFactory()
        request = factory.get(
            '/api/crm-vendas/leads/',
            HTTP_X_LOJA_ID=str(self.loja_b.id),
            HTTP_X_TENANT_SLUG=self.loja_b.slug,
        )
        request.user = self.owner_a
        self.assertFalse(ensure_loja_context(request))

    def test_user_can_access_loja_bloqueia_cross_tenant(self):
        from core.tenant_access import user_can_access_loja

        self.assertTrue(user_can_access_loja(self.owner_a, self.loja_a))
        self.assertFalse(user_can_access_loja(self.owner_a, self.loja_b))
        self.assertTrue(user_can_access_loja(self.owner_b, self.loja_b))


class VendedorFilterMixinPoolTest(SimpleTestCase):
    def setUp(self):
        from crm_vendas.mixins import VendedorFilterMixin

        class _LeadViewStub(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = ['oportunidades__vendedor_id']

        class _PoolViewStub(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_include_unassigned_pool = True

        self.factory = RequestFactory()
        self.view = _LeadViewStub()
        self.pool_view = _PoolViewStub()
        self.view.request = self.factory.get('/crm-vendas/leads/')
        self.pool_view.request = self.factory.get('/crm-vendas/leads/')

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=5)
    def test_pool_sem_vendedor_excluido_por_padrao(self, _vid, _owner):
        qs = MagicMock()
        qs.filter.return_value.distinct.return_value = 'filtered'

        result = self.view.filter_by_vendedor(qs)

        q_arg = qs.filter.call_args.args[0]
        self.assertIsInstance(q_arg, Q)
        self.assertNotIn('vendedor_id__isnull', str(q_arg))
        self.assertIs(result, 'filtered')

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=5)
    def test_pool_sem_vendedor_incluido_quando_flag_true(self, _vid, _owner):
        qs = MagicMock()
        qs.filter.return_value.distinct.return_value = 'pool'

        self.pool_view.filter_by_vendedor(qs)

        q_arg = qs.filter.call_args.args[0]
        self.assertIn('vendedor_id__isnull', str(q_arg))

    @patch('crm_vendas.utils.is_owner', return_value=True)
    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=5)
    def test_owner_ve_queryset_intacto(self, _vid, _owner):
        qs = MagicMock()
        result = self.view.filter_by_vendedor(qs)
        self.assertIs(result, qs)
        qs.filter.assert_not_called()
