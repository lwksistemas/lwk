"""Smoke de API HTTP — contas, contatos e atividades."""
from unittest.mock import MagicMock, patch

from .test_api_crm_integration import _CrmApiTestBase


class CrmContasApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.views_cadastros.ContaViewSet.get_queryset')
    @patch('crm_vendas.views_cadastros.get_current_loja_id')
    def test_list_contas_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.filter.return_value = chain
        mock_qs.return_value = chain
        response = self.client.get('/api/crm-vendas/contas/')
        self.assertEqual(response.status_code, 200, response.content)


class CrmContatosApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.views_cadastros.ContatoViewSet.get_queryset')
    @patch('crm_vendas.views_cadastros.get_current_loja_id')
    def test_list_contatos_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        mock_qs.return_value = []
        response = self.client.get('/api/crm-vendas/contatos/')
        self.assertEqual(response.status_code, 200, response.content)


class CrmAtividadesApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.views_pipelines.AtividadeViewSet.get_queryset')
    @patch('crm_vendas.views_pipelines.get_current_loja_id')
    def test_list_atividades_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.defer.return_value = chain
        mock_qs.return_value = chain
        response = self.client.get('/api/crm-vendas/atividades/')
        self.assertEqual(response.status_code, 200, response.content)
