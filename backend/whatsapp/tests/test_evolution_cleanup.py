"""Testes — limpeza Evolution (órfãs e duplicatas)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.evolution_cleanup import (
    find_instances_for_loja,
    find_stale_evolution_instances,
    loja_id_from_instance_name,
)
from whatsapp.evolution_client import loja_id_from_evolution_instance
from whatsapp.views_evolution_webhook import _loja_id_from_instance


class EvolutionCleanupParseTest(SimpleTestCase):
    def test_loja_id_com_sufixo(self):
        self.assertEqual(loja_id_from_instance_name('lwk_loja_4_99123'), 4)
        self.assertEqual(loja_id_from_instance_name('lwk_loja_4'), 4)

    @patch('whatsapp.evolution_cleanup.list_evolution_instances')
    def test_find_instances_for_loja(self, mock_list):
        mock_list.return_value = [
            {'instance_name': 'lwk_loja_4', 'loja_id': 4},
            {'instance_name': 'lwk_loja_4_123', 'loja_id': 4},
            {'instance_name': 'lwk_loja_9', 'loja_id': 9},
        ]
        rows = find_instances_for_loja(4)
        self.assertEqual(len(rows), 2)

    @patch('whatsapp.evolution_cleanup.list_evolution_instances')
    def test_find_stale_exclui_instancia_ativa(self, mock_list):
        mock_list.return_value = [
            {'instance_name': 'lwk_loja_4', 'loja_id': 4},
            {'instance_name': 'lwk_loja_4_555', 'loja_id': 4},
        ]
        stale = find_stale_evolution_instances({4: 'lwk_loja_4_555'})
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['instance_name'], 'lwk_loja_4')


class EvolutionWebhookInstanceParseTest(SimpleTestCase):
    def test_webhook_reconhece_instancia_rotacionada(self):
        self.assertEqual(loja_id_from_evolution_instance('lwk_loja_4_96990'), 4)
        self.assertEqual(_loja_id_from_instance('lwk_loja_4_96990'), 4)
