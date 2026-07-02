"""Smoke de API HTTP — oportunidades e financeiro CRM."""
from unittest.mock import MagicMock, patch

from .test_api_crm_integration import _CrmApiTestBase


class CrmOportunidadesApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.views_pipelines.OportunidadeViewSet.get_queryset')
    @patch('tenants.middleware.get_current_loja_id')
    def test_list_oportunidades_vazio(self, mock_loja_id, mock_qs):
        mock_loja_id.return_value = self.loja.id
        chain = MagicMock()
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.all.return_value = []
        mock_qs.return_value = chain
        response = self.client.get('/api/crm-vendas/oportunidades/')
        self.assertEqual(response.status_code, 200, response.content)


class CrmFinanceiroResumoApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.views_financeiro.resumo_financeiro_crm')
    @patch('crm_vendas.views_financeiro.garantir_grupos_padrao')
    @patch('crm_vendas.views_financeiro.get_current_loja_id')
    def test_financeiro_resumo_delega_servico(self, mock_loja_id, _grupos, mock_resumo):
        mock_loja_id.return_value = self.loja.id
        mock_resumo.return_value = {
            'receitas_pago': '0.00',
            'receitas_pendente': '0.00',
            'despesas_pago': '0.00',
            'despesas_pendente': '0.00',
        }
        response = self.client.get('/api/crm-vendas/financeiro/resumo/')
        self.assertEqual(response.status_code, 200, response.content)
        mock_resumo.assert_called_once()

    @patch('crm_vendas.views_financeiro.get_current_loja_id', return_value=None)
    def test_financeiro_resumo_sem_loja_retorna_400(self, _loja):
        response = self.client.get('/api/crm-vendas/financeiro/resumo/')
        self.assertEqual(response.status_code, 400)
