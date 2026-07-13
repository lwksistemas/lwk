"""Testes da view webhook Asaas por loja (CRM)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from crm_vendas.views_asaas_webhook import asaas_loja_webhook


@override_settings(DATABASES={"default": {}})
class AsaasLojaWebhookViewTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _loja(self):
        loja = MagicMock()
        loja.id = 4
        loja.slug = "41449198000172"
        return loja

    @patch("crm_vendas.views_asaas_webhook.resolve_loja_from_slug_or_cnpj", return_value=None)
    def test_slug_inexistente_404(self, _resolve):
        request = self.factory.get("/api/crm-vendas/webhooks/asaas/inexistente/")
        response = asaas_loja_webhook(request, loja_slug="inexistente")
        self.assertEqual(response.status_code, 404)

    @patch("crm_vendas.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    def test_get_confirma_webhook_ativo(self, mock_resolve):
        mock_resolve.return_value = self._loja()
        request = self.factory.get("/api/crm-vendas/webhooks/asaas/felix/")
        response = asaas_loja_webhook(request, loja_slug="felix")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("ok"))

    @patch("crm_vendas.views_asaas_webhook.process_asaas_loja_webhook_sync")
    @patch("asaas_integration.queue_dispatch.should_enqueue_asaas_webhook", return_value=False)
    @patch("core.webhook_security.verify_asaas_access_token", return_value=True)
    @patch("crm_vendas.models_config.CRMConfig.resolve_asaas_webhook_token", return_value="secret")
    @patch("crm_vendas.views_asaas_webhook._configure_tenant_db_for_loja", return_value=True)
    @patch("crm_vendas.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    def test_post_processa_sync(
        self,
        mock_resolve,
        _tenant,
        _token_cfg,
        _verify,
        _enqueue_flag,
        mock_sync,
    ):
        mock_resolve.return_value = self._loja()
        request = self.factory.post(
            "/api/crm-vendas/webhooks/asaas/felix/",
            {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_1"}},
            format="json",
        )
        force_authenticate(request, user=None)
        response = asaas_loja_webhook(request, loja_slug="felix")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("status"), "received")
        mock_sync.assert_called_once()
        self.assertEqual(mock_sync.call_args[0][0], 4)
        self.assertEqual(mock_sync.call_args[0][1]["event"], "PAYMENT_RECEIVED")

    @patch("asaas_integration.queue_dispatch.enqueue_asaas_loja_webhook")
    @patch("asaas_integration.queue_dispatch.should_enqueue_asaas_webhook", return_value=True)
    @patch("core.webhook_security.verify_asaas_access_token", return_value=True)
    @patch("crm_vendas.models_config.CRMConfig.resolve_asaas_webhook_token", return_value="secret")
    @patch("crm_vendas.views_asaas_webhook._configure_tenant_db_for_loja", return_value=True)
    @patch("crm_vendas.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    def test_post_enfileira_quando_fila_ativa(
        self,
        mock_resolve,
        _tenant,
        _token_cfg,
        _verify,
        _enqueue_flag,
        mock_enqueue,
    ):
        mock_resolve.return_value = self._loja()
        payload = {"event": "INVOICE_AUTHORIZED", "invoice": {"id": "inv_1"}}
        request = self.factory.post(
            "/api/crm-vendas/webhooks/asaas/felix/",
            payload,
            format="json",
        )
        response = asaas_loja_webhook(request, loja_slug="felix")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("queued"))
        mock_enqueue.assert_called_once_with(4, payload)

    @patch("core.webhook_security.webhook_auth_failed_response")
    @patch("core.webhook_security.verify_asaas_access_token", return_value=False)
    @patch("crm_vendas.models_config.CRMConfig.resolve_asaas_webhook_token", return_value="secret")
    @patch("crm_vendas.views_asaas_webhook._configure_tenant_db_for_loja", return_value=True)
    @patch("crm_vendas.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    def test_post_token_invalido(self, mock_resolve, _tenant, _token_cfg, _verify, mock_fail):
        from rest_framework.response import Response

        mock_resolve.return_value = self._loja()
        mock_fail.return_value = Response({"detail": "Unauthorized"}, status=401)
        request = self.factory.post("/api/crm-vendas/webhooks/asaas/felix/", {}, format="json")
        response = asaas_loja_webhook(request, loja_slug="felix")
        self.assertEqual(response.status_code, 401)
