"""Smoke de API HTTP — propostas, contratos e assinatura pública."""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from .test_api_crm_integration import _CrmApiTestBase


class CrmPropostasApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.views_documentos.PropostaViewSet.get_queryset")
    @patch("tenants.middleware.get_current_loja_id")
    def test_list_propostas_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.all.return_value = []
        mock_qs.return_value = chain
        response = self.client.get("/api/crm-vendas/propostas/")
        self.assertEqual(response.status_code, 200, response.content)


class CrmContratosApiSmokeTest(_CrmApiTestBase):
    @patch("crm_vendas.views_documentos.ContratoViewSet.get_queryset")
    @patch("tenants.middleware.get_current_loja_id")
    def test_list_contratos_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.all.return_value = []
        mock_qs.return_value = chain
        response = self.client.get("/api/crm-vendas/contratos/")
        self.assertEqual(response.status_code, 200, response.content)


class CrmAssinaturaPublicaApiSmokeTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_token_invalido_retorna_erro(self):
        response = self.client.get("/api/crm-vendas/assinar/token-invalido-xyz/")
        self.assertIn(response.status_code, (400, 404))
        data = response.json()
        self.assertTrue("detail" in data or "erro" in data or "error" in data)
