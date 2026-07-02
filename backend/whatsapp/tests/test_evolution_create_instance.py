"""Testes — criação/recriação de instância Evolution com QR."""
from unittest.mock import patch

from django.test import SimpleTestCase

from whatsapp.evolution_client import EvolutionAPIError, create_evolution_instance_with_qr


class CreateEvolutionInstanceWithQrTest(SimpleTestCase):
    @patch('whatsapp.evolution_client.recreate_instance', return_value={'base64': 'qr'})
    @patch('whatsapp.evolution_client.instance_exists', return_value=True)
    def test_recria_quando_instancia_ja_existe(self, _exists, mock_recreate):
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_recreate.assert_called_once_with('lwk_loja_4')
        self.assertEqual(data['base64'], 'qr')

    @patch('whatsapp.evolution_client.create_instance', return_value={'base64': 'new'})
    @patch('whatsapp.evolution_client.instance_exists', return_value=False)
    def test_cria_quando_nao_existe(self, _exists, mock_create):
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_create.assert_called_once_with('lwk_loja_4')
        self.assertEqual(data['base64'], 'new')

    @patch('whatsapp.evolution_client.recreate_instance', return_value={'base64': 'recreated'})
    @patch('whatsapp.evolution_client.create_instance')
    @patch('whatsapp.evolution_client.instance_exists', return_value=False)
    def test_recria_apos_bad_request_no_create(self, _exists, mock_create, mock_recreate):
        mock_create.side_effect = EvolutionAPIError('Bad Request', status_code=400)
        data = create_evolution_instance_with_qr('lwk_loja_4')
        mock_recreate.assert_called_once_with('lwk_loja_4')
        self.assertEqual(data['base64'], 'recreated')
