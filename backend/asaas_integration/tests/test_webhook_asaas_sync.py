"""Sincroniza o token do webhook LWK com o painel Asaas."""
from unittest.mock import patch

from django.test import SimpleTestCase

from asaas_integration.webhook_asaas_sync import sincronizar_token_webhook_asaas


class SincronizarTokenWebhookAsaasTests(SimpleTestCase):
    @patch("asaas_integration.models.AsaasConfig")
    def test_sem_token(self, MockCfg):
        MockCfg.resolve_webhook_token.return_value = "curto"
        MockCfg.resolve_api_key.return_value = "chave"
        self.assertFalse(sincronizar_token_webhook_asaas()["success"])

    @patch("asaas_integration.models.AsaasConfig")
    def test_sem_chave_api(self, MockCfg):
        MockCfg.resolve_webhook_token.return_value = "t" * 40
        MockCfg.resolve_api_key.return_value = ""
        self.assertFalse(sincronizar_token_webhook_asaas()["success"])

    @patch("asaas_integration.client.AsaasClient")
    @patch("asaas_integration.models.AsaasConfig")
    def test_webhook_nao_encontrado(self, MockCfg, MockClient):
        MockCfg.resolve_webhook_token.return_value = "t" * 40
        MockCfg.resolve_api_key.return_value = "chave"
        MockCfg.effective_sandbox.return_value = False
        MockClient.return_value._make_request.return_value = {"data": []}
        out = sincronizar_token_webhook_asaas()
        self.assertFalse(out["success"])
        self.assertIn("não encontrado", out["error"])

    @patch("asaas_integration.client.AsaasClient")
    @patch("asaas_integration.models.AsaasConfig")
    def test_grava_auth_token_no_webhook_lwk(self, MockCfg, MockClient):
        MockCfg.resolve_webhook_token.return_value = "t" * 40
        MockCfg.resolve_api_key.return_value = "chave"
        MockCfg.effective_sandbox.return_value = False
        client = MockClient.return_value
        client._make_request.side_effect = [
            {
                "data": [
                    {
                        "id": "wh_1",
                        "name": "LWK SISTEMAS",
                        "url": "https://api.lwksistemas.com.br/api/asaas/webhook/",
                        "email": "a@b.com",
                        "sendType": "SEQUENTIALLY",
                        "events": ["PAYMENT_CREATED"],
                    }
                ]
            },
            {},
        ]
        out = sincronizar_token_webhook_asaas()
        self.assertTrue(out["success"])
        put = client._make_request.call_args_list[1]
        self.assertEqual(put.args[0], "PUT")
        self.assertIn("wh_1", put.args[1])
        body = put.args[2]
        self.assertEqual(body["authToken"], "t" * 40)
        self.assertTrue(body["enabled"])
        self.assertFalse(body["interrupted"])
        self.assertIn("PAYMENT_RECEIVED", body["events"])
        self.assertIn("PAYMENT_CONFIRMED", body["events"])
