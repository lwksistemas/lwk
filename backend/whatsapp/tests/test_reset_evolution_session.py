"""Testes — reset de sessão Evolution (WhatsApp Web)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.connection_service import reset_evolution_connection
from whatsapp.models import WhatsAppConfig


class ResetEvolutionConnectionTest(SimpleTestCase):
    @patch('whatsapp.connection_service._apply_qr_from_data', return_value={'connection_status': 'qr_pending'})
    @patch('whatsapp.connection_service._obtain_evolution_qr', return_value=({'base64': 'qr'}, 'lwk_loja_6_123'))
    @patch('whatsapp.connection_service._rotate_evolution_instance_name', return_value='lwk_loja_6_123')
    @patch('whatsapp.connection_service._prepare_evolution_qr_config')
    @patch('whatsapp.evolution_cleanup.delete_evolution_for_loja', return_value={'ok': True})
    @patch('whatsapp.connection_service.logout_instance')
    @patch('whatsapp.connection_service.evolution_configured', return_value=True)
    @patch('whatsapp.connection_service.ensure_evolution_instance_name', return_value='lwk_loja_6')
    def test_reset_apaga_instancia_e_cria_qr(
        self, _name, _cfg, _logout, _delete, _prepare, _rotate, _obtain, _apply,
    ):
        config = MagicMock()
        config.loja_id = 6
        config.whatsapp_provider = WhatsAppConfig.PROVIDER_EVOLUTION

        result = reset_evolution_connection(config)

        _logout.assert_called_once_with('lwk_loja_6')
        _delete.assert_called_once()
        _rotate.assert_called_once()
        _obtain.assert_called_once()
        self.assertEqual(result['connection_status'], 'qr_pending')
