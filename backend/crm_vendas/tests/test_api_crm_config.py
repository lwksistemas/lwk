"""Smoke de API HTTP — configuração CRM."""
from unittest.mock import MagicMock, patch

from .test_api_crm_integration import _CrmApiTestBase


class CrmConfigApiSmokeTest(_CrmApiTestBase):
    @patch('crm_vendas.serializers.CRMConfigSerializer')
    @patch('crm_vendas.views_crm_config_api._get_crm_config_for_loja')
    @patch('crm_vendas.views_crm_config_api.get_current_loja_id')
    def test_get_config_retorna_dados(self, mock_loja_id, mock_get_config, mock_serializer):
        mock_loja_id.return_value = self.loja.id
        mock_get_config.return_value = MagicMock()
        mock_serializer.return_value.data = {'loja_id': self.loja.id, 'origens_lead': []}
        response = self.client.get('/api/crm-vendas/config/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json().get('loja_id'), self.loja.id)

    @patch('crm_vendas.views_crm_config_api.get_current_loja_id', return_value=None)
    def test_get_config_sem_loja_retorna_400(self, _loja):
        response = self.client.get('/api/crm-vendas/config/')
        self.assertEqual(response.status_code, 400)
