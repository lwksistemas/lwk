"""Testes — reset de sessão Evolution (WhatsApp Web)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.connection_service import reset_evolution_connection
from whatsapp.models import WhatsAppConfig


class ResetEvolutionConnectionTest(SimpleTestCase):
    @patch('whatsapp.connection_service._invalidate_whatsapp_config_cache')
    @patch('whatsapp.connection_service.instance_exists', return_value=False)
    @patch('whatsapp.connection_service._apply_qr_from_data', return_value={'connection_status': 'qr_pending'})
    @patch('whatsapp.connection_service.create_instance', return_value={'base64': 'qr'})
    @patch('whatsapp.evolution_cleanup.delete_evolution_for_loja', return_value={'ok': True})
    @patch('whatsapp.connection_service.logout_instance')
    @patch('whatsapp.connection_service.evolution_configured', return_value=True)
    @patch('whatsapp.connection_service.ensure_evolution_instance_name', return_value='lwk_loja_6')
    def test_reset_apaga_instancia_e_cria_qr(
        self, _name, _cfg, _logout, _delete, _create, mock_apply, _exists, _cache,
    ):
        config = MagicMock()
        config.loja_id = 6
        config.whatsapp_provider = WhatsAppConfig.PROVIDER_EVOLUTION

        result = reset_evolution_connection(config)

        _logout.assert_called_once_with('lwk_loja_6')
        _delete.assert_called_once()
        _create.assert_called_once_with('lwk_loja_6')
        self.assertEqual(result['connection_status'], 'qr_pending')
        self.assertEqual(config.whatsapp_connection_status, WhatsAppConfig.CONNECTION_QR_PENDING)
