"""Testes — webhook Evolution e confirmação de agenda por texto."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.connection_service import _ensure_evolution_webhook, _invalidate_evolution_webhook_cache
from whatsapp.services import enviar_confirmacao_agendamento
from whatsapp.sync_context import whatsapp_sync_only


class EvolutionWebhookCacheTest(SimpleTestCase):
    def setUp(self):
        _invalidate_evolution_webhook_cache()

    def tearDown(self):
        _invalidate_evolution_webhook_cache()

    @patch('whatsapp.evolution_client.set_instance_webhook')
    def test_webhook_configurado_apenas_uma_vez_por_instancia(self, mock_set):
        _ensure_evolution_webhook('lwk_loja_6')
        _ensure_evolution_webhook('lwk_loja_6')
        mock_set.assert_called_once()


class EnviarConfirmacaoAgendamentoTest(SimpleTestCase):
    @patch('whatsapp.services.send_whatsapp')
    @patch('whatsapp.services.msg_confirmacao', return_value='Olá Cliente 😊\n\n🔗 https://link')
    @patch('clinica_beleza.agenda_confirmacao_service.url_confirmacao_frontend', return_value='https://lwksistemas.com.br/confirmar/x')
    @patch('clinica_beleza.agenda_confirmacao_service.gerar_token_confirmacao', return_value='tok-front')
    def test_envia_mensagem_original_sincrona(self, _tok, _url, _msg, mock_send):
        mock_send.return_value = (True, None)
        agendamento = MagicMock()
        agendamento.patient.phone = '5516981402966'
        agendamento.loja_id = 6
        agendamento.id = 7

        sync_durante_envio = []

        def capturar(**kwargs):
            sync_durante_envio.append(whatsapp_sync_only.get())
            self.assertEqual(kwargs['mensagem'], 'Olá Cliente 😊\n\n🔗 https://link')
            return True, None

        mock_send.side_effect = capturar

        ok, err = enviar_confirmacao_agendamento(agendamento, config=MagicMock())

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(sync_durante_envio, [True])
