"""Testes — webhook Evolution connection.update."""
import json
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from whatsapp.connection_service import update_evolution_connection_from_webhook
from whatsapp.models import WhatsAppConfig
from whatsapp.views_evolution_webhook import EvolutionWebhookView


class UpdateEvolutionConnectionFromWebhookTest(SimpleTestCase):
    @patch("whatsapp.connection_service._invalidate_whatsapp_config_cache")
    @patch("whatsapp.connection_service._sync_whatsapp_status_to_public")
    @patch("whatsapp.connection_service._apply_evolution_state_to_config")
    @patch("tenants.middleware.set_current_tenant_db")
    @patch("tenants.middleware.set_current_loja_id")
    @patch("core.db_config.ensure_loja_database_config", return_value=True)
    @patch("django.conf.settings")
    @patch("superadmin.models.Loja")
    @patch("whatsapp.connection_service.WhatsAppConfig")
    def test_marca_desconectado_quando_state_close(
        self,
        mock_config_cls,
        mock_loja_cls,
        mock_settings,
        _ensure_db,
        mock_set_loja,
        mock_set_db,
        mock_apply,
        _sync_public,
        _invalidate_cache,
    ):
        loja = MagicMock()
        loja.database_name = "loja_test"
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja
        mock_settings.DATABASES = {"loja_test": {}}

        config = MagicMock()
        config.loja_id = 6
        mock_config_cls.objects.filter.return_value.first.return_value = config

        update_evolution_connection_from_webhook(6, {"state": "close"})

        mock_set_loja.assert_called_once_with(6)
        mock_set_db.assert_called_once_with("loja_test")
        mock_apply.assert_called_once()
        args = mock_apply.call_args[0]
        self.assertEqual(args[0], config)
        self.assertEqual(args[1], WhatsAppConfig.CONNECTION_DISCONNECTED)


class EvolutionWebhookConnectionUpdateTest(SimpleTestCase):
    @patch("whatsapp.connection_service.update_evolution_connection_from_webhook")
    @patch.object(EvolutionWebhookView, "_authenticate_webhook", return_value=True)
    def test_post_connection_update_chama_handler(self, _auth, mock_update):
        factory = RequestFactory()
        body = {
            "event": "connection.update",
            "instance": "lwk_loja_6",
            "data": {"state": "close"},
        }
        request = factory.post(
            "/api/whatsapp/evolution/webhook/",
            data=json.dumps(body),
            content_type="application/json",
        )
        response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        mock_update.assert_called_once_with(6, {"state": "close"})
