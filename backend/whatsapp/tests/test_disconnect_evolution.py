"""Testes — desconexão e sync Evolution (sessão fantasma)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.connection_service import disconnect_evolution, sync_evolution_connection
from whatsapp.evolution_client import EvolutionAPIError
from whatsapp.models import WhatsAppConfig


class DisconnectEvolutionTest(SimpleTestCase):
    @patch("whatsapp.evolution_cleanup.delete_all_evolution_instances_for_loja", return_value=[])
    @patch("whatsapp.connection_service._invalidate_whatsapp_config_cache")
    @patch("whatsapp.connection_service._sync_whatsapp_status_to_public")
    @patch("whatsapp.connection_service.logout_instance")
    @patch("whatsapp.connection_service.ensure_evolution_instance_name", return_value="lwk_loja_9")
    def test_disconnect_nao_chama_sync_que_reverte_status(
        self, _name, _logout, _sync_public, _cache, _delete_all,
    ):
        config = MagicMock()
        config.loja_id = 9
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_CONNECTED
        config.whatsapp_connected_phone = "5511999999999"
        config.whatsapp_connected_at = None

        with patch("whatsapp.connection_service.sync_evolution_connection") as mock_sync:
            result = disconnect_evolution(config)

        mock_sync.assert_not_called()
        _delete_all.assert_called_once_with(9)
        self.assertEqual(config.whatsapp_connection_status, WhatsAppConfig.CONNECTION_DISCONNECTED)
        self.assertEqual(result["connection_status"], "disconnected")


class SyncEvolutionStaleSessionTest(SimpleTestCase):
    @patch("whatsapp.connection_service._ensure_evolution_webhook")
    @patch("whatsapp.connection_service.get_connection_state")
    @patch("whatsapp.connection_service.evolution_configured", return_value=True)
    @patch("whatsapp.connection_service.ensure_evolution_instance_name", return_value="lwk_loja_9")
    def test_sync_nao_promove_disconnected_para_connected(
        self, _name, _cfg, mock_state, _webhook,
    ):
        config = MagicMock()
        config.loja_id = 9
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_DISCONNECTED
        config.whatsapp_connected_phone = ""
        config.whatsapp_connected_at = None
        mock_state.return_value = {"state": "connected", "phone": "5511999999999"}

        result = sync_evolution_connection(config, fetch_qr=False)

        self.assertEqual(result["connection_status"], "disconnected")
        config.save.assert_not_called()

    @patch("whatsapp.connection_service._apply_evolution_state_to_config")
    @patch("whatsapp.connection_service.get_connection_state")
    @patch("whatsapp.connection_service.evolution_configured", return_value=True)
    @patch("whatsapp.connection_service.ensure_evolution_instance_name", return_value="lwk_loja_9")
    def test_sync_promove_qr_pending_para_connected(
        self, _name, _cfg, mock_state, mock_apply,
    ):
        config = MagicMock()
        config.loja_id = 9
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_QR_PENDING
        config.whatsapp_connected_phone = ""
        config.whatsapp_connected_at = None
        mock_state.return_value = {"state": "connected", "phone": "5511999999999"}

        sync_evolution_connection(config, fetch_qr=False)

        mock_apply.assert_called_once()

    @patch("whatsapp.connection_service._apply_evolution_state_to_config")
    @patch("whatsapp.connection_service.get_connection_state")
    @patch("whatsapp.connection_service.evolution_configured", return_value=True)
    @patch("whatsapp.connection_service.ensure_evolution_instance_name", return_value="lwk_loja_9")
    def test_sync_404_marca_desconectado(self, _name, _cfg, mock_state, mock_apply):
        config = MagicMock()
        config.loja_id = 9
        config.whatsapp_connection_status = WhatsAppConfig.CONNECTION_CONNECTED
        config.whatsapp_connected_phone = "5511999999999"
        config.whatsapp_connected_at = None
        mock_state.side_effect = EvolutionAPIError("not found", status_code=404)

        sync_evolution_connection(config, fetch_qr=False)

        mock_apply.assert_called_once_with(config, WhatsAppConfig.CONNECTION_DISCONNECTED)
