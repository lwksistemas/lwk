"""Salvar token de webhook sem apagar a chave/integração Asaas."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from asaas_integration.views_config.config_views import _asaas_config_post


class AsaasConfigPostTests(SimpleTestCase):
    def _config(self):
        config = MagicMock()
        config.enabled = True
        config.sandbox = False
        config.api_key_masked = "$aact_p...1234"
        config.webhook_token_decrypted = "t" * 40
        config.webhook_token_masked = "tttttt...tttt"
        return config

    @patch("asaas_integration.views_config.config_views._asaas_webhook_url", return_value="https://api.example/api/asaas/webhook/")
    @patch("asaas_integration.views_config.config_views.AsaasConfig")
    def test_salva_so_o_token_e_mantem_enabled(self, MockCfg, _url):
        config = self._config()
        MockCfg.resolve_webhook_token.return_value = "t" * 40
        MockCfg.resolve_api_key.return_value = "chave"
        request = MagicMock()
        request.data = {"webhook_token": "b" * 40}
        resp = _asaas_config_post(request, config, resolved_key="chave-existente")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(config.webhook_token, "b" * 40)
        self.assertTrue(config.enabled)
        config.save.assert_called_once()
        self.assertTrue(resp.data["webhook_token_configured"])

    @patch("asaas_integration.views_config.config_views._asaas_webhook_url", return_value="https://api.example/api/asaas/webhook/")
    @patch("asaas_integration.views_config.config_views.AsaasConfig")
    def test_token_curto_falha(self, MockCfg, _url):
        config = self._config()
        request = MagicMock()
        request.data = {"webhook_token": "curto"}
        resp = _asaas_config_post(request, config, resolved_key="chave")
        self.assertEqual(resp.status_code, 400)
        config.save.assert_not_called()
