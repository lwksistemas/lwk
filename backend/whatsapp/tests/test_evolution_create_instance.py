"""Testes — criação/recriação de instância Evolution com QR."""
from unittest.mock import patch

from django.test import SimpleTestCase

from whatsapp.evolution_client import (
    EvolutionAPIError,
    connect_instance_for_qr,
    create_evolution_instance_with_qr,
    delete_instance,
    logout_instance,
)


class CreateEvolutionInstanceWithQrTest(SimpleTestCase):
    @patch('whatsapp.evolution_client.connect_instance_for_qr', return_value={'base64': 'qr'})
    @patch('whatsapp.evolution_client.instance_exists', return_value=True)
    def test_prioriza_connect_quando_instancia_existe(self, _exists, mock_connect):
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_connect.assert_called_once_with('lwk_loja_4', wait_attempts=8, wait_delay=2.0)
        self.assertEqual(data['base64'], 'qr')

    @patch('whatsapp.evolution_client.recreate_instance', return_value={'base64': 'qr'})
    @patch('whatsapp.evolution_client.connect_instance_for_qr', return_value={})
    @patch('whatsapp.evolution_client.instance_exists', return_value=True)
    def test_recria_quando_connect_sem_qr(self, _exists, _connect, mock_recreate):
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_recreate.assert_called_once_with('lwk_loja_4')
        self.assertEqual(data['base64'], 'qr')

    @patch('whatsapp.evolution_client.create_instance', return_value={'base64': 'new'})
    @patch('whatsapp.evolution_client.instance_exists', return_value=False)
    def test_cria_quando_nao_existe(self, _exists, mock_create):
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_create.assert_called_once_with('lwk_loja_4')
        self.assertEqual(data['base64'], 'new')


class EvolutionBestEffortDeleteTest(SimpleTestCase):
    @patch('whatsapp.evolution_client._request', return_value={})
    def test_delete_ignora_400(self, mock_request):
        mock_request.side_effect = [
            EvolutionAPIError('Bad Request', status_code=400),
        ]
        result = delete_instance('lwk_loja_4')
        self.assertEqual(result, {})

    @patch('whatsapp.evolution_client._request', return_value={})
    def test_logout_ignora_500(self, mock_request):
        mock_request.side_effect = [
            EvolutionAPIError('Internal Server Error', status_code=500),
        ]
        result = logout_instance('lwk_loja_4')
        self.assertEqual(result, {})
