from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import (
    _agendar_confirmacao_reagendamento,
    _redisparar_confirmacao_por_mudanca_data,
)


class RedispararConfirmacaoReagendamentoTest(SimpleTestCase):
    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_agenda_envio_em_segundo_plano(self, mock_envio, mock_config, mock_agendar):
        appointment = MagicMock(id=82, loja_id=6)
        mock_config.objects.filter.return_value.first.return_value = MagicMock(
            whatsapp_ativo=True,
            enviar_confirmacao=True,
        )

        _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_envio.objects.filter.assert_called_once_with(appointment_id=82)
        mock_agendar.assert_called_once_with(82, 6)

    @patch("whatsapp.services.enviar_confirmacao_agendamento")
    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_nao_chama_evolution_no_request(
        self, mock_envio, mock_config, mock_agendar, mock_enviar,
    ):
        appointment = MagicMock(id=82, loja_id=6)
        mock_config.objects.filter.return_value.first.return_value = MagicMock(
            whatsapp_ativo=True,
            enviar_confirmacao=True,
        )

        _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_enviar.assert_not_called()
        mock_agendar.assert_called_once()


class AgendarConfirmacaoReagendamentoTest(SimpleTestCase):
    @patch("django_q.tasks.async_task")
    @patch("core.task_queue.task_queue_enabled", return_value=True)
    def test_usa_fila_quando_habilitada(self, _enabled, mock_async):
        _agendar_confirmacao_reagendamento(82, 6)
        mock_async.assert_called_once_with(
            "clinica_beleza.agenda_service.enviar_confirmacao_reagendamento",
            82,
            6,
            task_name="agenda-reagend-82",
        )

    @patch("threading.Thread")
    @patch("core.task_queue.task_queue_enabled", return_value=False)
    def test_usa_thread_sem_fila(self, _enabled, mock_thread):
        _agendar_confirmacao_reagendamento(82, 6)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
