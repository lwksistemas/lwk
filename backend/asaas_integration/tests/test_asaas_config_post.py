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

    @patch(
        "asaas_integration.webhook_asaas_sync.sincronizar_token_webhook_asaas",
        return_value={"success": True, "webhook_id": "wh_1"},
    )
    @patch("asaas_integration.views_config.config_views._asaas_webhook_url", return_value="https://api.example/api/asaas/webhook/")
    @patch("asaas_integration.views_config.config_views.AsaasConfig")
    def test_salva_so_o_token_e_mantem_enabled(self, MockCfg, _url, mock_sync):
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
        mock_sync.assert_called_once()
        self.assertTrue(resp.data["asaas_webhook_sync"]["success"])

    @patch("asaas_integration.views_config.config_views._asaas_webhook_url", return_value="https://api.example/api/asaas/webhook/")
    @patch("asaas_integration.views_config.config_views.AsaasConfig")
    def test_token_curto_falha(self, MockCfg, _url):
        config = self._config()
        request = MagicMock()
        request.data = {"webhook_token": "curto"}
        resp = _asaas_config_post(request, config, resolved_key="chave")
        self.assertEqual(resp.status_code, 400)
        config.save.assert_not_called()


class AsaasConfigViewDecoratorTests(SimpleTestCase):
    def test_asaas_config_tem_api_view(self):
        from asaas_integration.views_config.config_views import asaas_config

        self.assertTrue(
            hasattr(asaas_config, "cls"),
            "asaas_config precisa de @api_view — sem isso GET/POST não gravam o token",
        )

    def test_get_anonimo_nao_acessa_config(self):
        from rest_framework.test import APIRequestFactory

        from asaas_integration.views_config.config_views import asaas_config

        request = APIRequestFactory().get("/api/asaas/config/")
        resp = asaas_config(request)
        self.assertIn(resp.status_code, (401, 403))
