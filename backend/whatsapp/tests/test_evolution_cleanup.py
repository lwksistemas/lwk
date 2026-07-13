"""Testes — limpeza Evolution (órfãs e duplicatas)."""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from whatsapp.evolution_cleanup import (
    evolution_shared_with_other_environment,
    find_cross_environment_evolution_instances,
    find_instances_for_loja,
    find_stale_evolution_instances,
    loja_id_from_instance_name,
)
from whatsapp.evolution_client import loja_id_from_evolution_instance
from whatsapp.views_evolution_webhook import _loja_id_from_instance


class EvolutionCleanupParseTest(SimpleTestCase):
    def test_loja_id_com_sufixo(self):
        self.assertEqual(loja_id_from_instance_name("lwk_loja_4_99123"), 4)
        self.assertEqual(loja_id_from_instance_name("lwk_loja_4"), 4)

    @patch("whatsapp.evolution_cleanup.list_evolution_instances")
    def test_find_instances_for_loja(self, mock_list):
        mock_list.return_value = [
            {"instance_name": "lwk_loja_4", "loja_id": 4},
            {"instance_name": "lwk_loja_4_123", "loja_id": 4},
            {"instance_name": "lwk_loja_9", "loja_id": 9},
        ]
        rows = find_instances_for_loja(4)
        self.assertEqual(len(rows), 2)

    @patch("whatsapp.evolution_cleanup.list_evolution_instances")
    def test_find_stale_exclui_instancia_ativa(self, mock_list):
        mock_list.return_value = [
            {"instance_name": "lwk_loja_4", "loja_id": 4},
            {"instance_name": "lwk_loja_4_555", "loja_id": 4},
        ]
        stale = find_stale_evolution_instances({4: "lwk_loja_4_555"})
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["instance_name"], "lwk_loja_4")


class EvolutionCrossEnvironmentTest(SimpleTestCase):
    @patch("whatsapp.evolution_cleanup.list_evolution_instances")
    @override_settings(EVOLUTION_DEDICATED=False)
    def test_detecta_instancias_de_outro_ambiente(self, mock_list):
        mock_list.return_value = [
            {"instance_name": "lwk_loja_11_4327", "loja_id": 11},
            {"instance_name": "lwk_loja_4_96990", "loja_id": 4},
        ]
        local_lojas = {11, 12}
        cross = find_cross_environment_evolution_instances(local_lojas)
        self.assertEqual(len(cross), 1)
        self.assertEqual(cross[0]["instance_name"], "lwk_loja_4_96990")
        self.assertTrue(evolution_shared_with_other_environment(local_lojas))

    @patch("whatsapp.evolution_cleanup.list_evolution_instances")
    @override_settings(EVOLUTION_DEDICATED=True)
    def test_evolution_dedicada_nao_marca_compartilhada(self, mock_list):
        mock_list.return_value = [
            {"instance_name": "lwk_loja_11", "loja_id": 11},
        ]
        self.assertFalse(evolution_shared_with_other_environment({11}))


class EvolutionWebhookInstanceParseTest(SimpleTestCase):
    def test_webhook_reconhece_instancia_rotacionada(self):
        self.assertEqual(loja_id_from_evolution_instance("lwk_loja_4_96990"), 4)
        self.assertEqual(_loja_id_from_instance("lwk_loja_4_96990"), 4)
