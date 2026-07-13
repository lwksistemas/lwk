"""Smoke de API HTTP — CRM Vendas (auth + contexto de loja)."""
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from superadmin.authentication import invalidate_session_cache
from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from superadmin.session_manager import SessionManager


class _CrmApiTestBase(TestCase):
    databases = {"default"}

    def setUp(self):
        uid = uuid.uuid4().hex[:10]
        self.tipo = TipoLoja.objects.create(
            nome="Tipo Teste API",
            slug=f"crm-api-{uid}",
            codigo=f"K{uid[:3]}",
        )
        self.plano = PlanoAssinatura.objects.create(
            nome="API CRM",
            slug=f"plano-api-{uid}",
            preco_mensal=99,
        )
        self.owner = User.objects.create_user(
            username=f"owner-api-{uid}@test.com",
            email=f"owner-api-{uid}@test.com",
            password="pass12345",
        )
        self.loja = Loja.objects.create(
            nome="CRM API Test",
            slug=f"crm-loja-{uid}",
            cpf_cnpj=f"33333333{uid[:6]}",
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner,
            database_created=True,
        )
        invalidate_session_cache(self.owner.id)
        self.client = APIClient()
        token = self._bearer_token()
        sid = SessionManager.create_session(self.owner.id, token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_SESSION_ID=sid,
            HTTP_X_LOJA_ID=str(self.loja.id),
            HTTP_X_TENANT_SLUG=self.loja.slug,
        )

    def _bearer_token(self) -> str:
        from rest_framework_simplejwt.tokens import RefreshToken

        return str(RefreshToken.for_user(self.owner).access_token)


class CrmMeApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.views_crm_me_dashboard.get_current_vendedor_id", return_value=None)
    @patch("crm_vendas.views_crm_me_dashboard.ensure_loja_context")
    @patch("crm_vendas.views_crm_me_dashboard.get_current_loja_id")
    def test_crm_me_owner_administrador(self, mock_loja_id, _ctx, _vend):
        mock_loja_id.return_value = self.loja.id
        response = self.client.get("/api/crm-vendas/me/")
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertFalse(data.get("is_vendedor"))
        self.assertEqual(data.get("user_role"), "administrador")
        self.assertTrue(data.get("acesso_total"))
        self.assertIsInstance(data.get("permissoes"), list)

    @patch("crm_vendas.views_crm_me_dashboard.ensure_loja_context")
    @patch("crm_vendas.views_crm_me_dashboard.get_current_loja_id", return_value=None)
    def test_crm_me_sem_loja_retorna_defaults(self, _loja, _ctx):
        response = self.client.get("/api/crm-vendas/me/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json().get("vendedor_id"))


class CrmDashboardApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.services_dashboard.build_dashboard_payload")
    @patch("crm_vendas.views_crm_me_dashboard.ensure_loja_context")
    @patch("crm_vendas.views_crm_me_dashboard.get_current_loja_id")
    def test_dashboard_delega_servico(self, mock_loja_id, _ctx, mock_build):
        mock_loja_id.return_value = self.loja.id
        mock_build.return_value = {"leads": 0, "oportunidades": 0, "receita": 0}
        response = self.client.get("/api/crm-vendas/dashboard/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json().get("leads"), 0)
        mock_build.assert_called_once()


class CrmLeadsApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.views_cadastros.LeadViewSet.get_queryset")
    @patch("tenants.middleware.get_current_loja_id")
    def test_list_leads_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.all.return_value = []
        mock_qs.return_value = chain
        response = self.client.get("/api/crm-vendas/leads/")
        self.assertEqual(response.status_code, 200, response.content)


class CrmBuscaApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.views_crm_busca.get_current_loja_id", return_value=None)
    def test_busca_sem_loja_retorna_vazio(self, _loja):
        response = self.client.get("/api/crm-vendas/busca/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["leads"], [])

    @patch("crm_vendas.views_crm_busca.is_owner", return_value=True)
    @patch("crm_vendas.views_crm_busca.get_current_vendedor_id", return_value=None)
    @patch("crm_vendas.models.Proposta")
    @patch("crm_vendas.models.Conta")
    @patch("crm_vendas.models.Oportunidade")
    @patch("crm_vendas.models.Lead")
    @patch("crm_vendas.views_crm_busca.get_current_loja_id")
    def test_busca_com_termo_chama_models(
        self, mock_loja_id, mock_lead, mock_opp, mock_conta, mock_prop, _vend, _owner,
    ):
        mock_loja_id.return_value = self.loja.id
        for mock_model in (mock_lead, mock_opp, mock_conta, mock_prop):
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.distinct.return_value = chain
            chain.values.return_value = chain
            chain.__getitem__ = lambda self, key: []
            mock_model.objects = MagicMock()
            mock_model.objects.filter.return_value = chain
        response = self.client.get("/api/crm-vendas/busca/?q=maria")
        self.assertEqual(response.status_code, 200)
        self.assertIn("leads", response.json())

    @patch("crm_vendas.views_crm_busca.is_owner", return_value=False)
    @patch("crm_vendas.views_crm_busca.get_current_vendedor_id", return_value=7)
    @patch("crm_vendas.models.Proposta")
    @patch("crm_vendas.models.Conta")
    @patch("crm_vendas.models.Oportunidade")
    @patch("crm_vendas.models.Lead")
    @patch("crm_vendas.views_crm_busca.get_current_loja_id")
    def test_busca_vendedor_nao_ve_pool_sem_dono(
        self, mock_loja_id, mock_lead, mock_opp, mock_conta, mock_prop, _vend, _owner,
    ):
        mock_loja_id.return_value = self.loja.id
        lead_chain = MagicMock()
        lead_chain.filter.return_value = lead_chain
        lead_chain.distinct.return_value = lead_chain
        lead_chain.values.return_value = lead_chain
        lead_chain.__getitem__ = lambda self, key: []
        mock_lead.objects = MagicMock()
        mock_lead.objects.filter.return_value = lead_chain
        for mock_model in (mock_opp, mock_conta, mock_prop):
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.distinct.return_value = chain
            chain.values.return_value = chain
            chain.__getitem__ = lambda self, key: []
            mock_model.objects = MagicMock()
            mock_model.objects.filter.return_value = chain

        response = self.client.get("/api/crm-vendas/busca/?q=maria")
        self.assertEqual(response.status_code, 200)

        lead_filter_q = lead_chain.filter.call_args.args[0]
        self.assertNotIn("vendedor_id__isnull", str(lead_filter_q))
