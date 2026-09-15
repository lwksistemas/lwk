from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.agenda_service import (
    _agendar_confirmacao_reagendamento,
    _redisparar_confirmacao_por_mudanca_data,
)


def _config_ok():
    return MagicMock(whatsapp_ativo=True, enviar_confirmacao=True, confirmacao_antecedencias_dias=[1])


class RedispararConfirmacaoReagendamentoTest(SimpleTestCase):
    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.confirmacao_agenda_service.antecedencias_da_config", return_value=[1])
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_nao_envia_ao_corrigir_horario_antes_do_dia_da_regra(
        self, mock_envio, mock_config, _antec, mock_agendar,
    ):
        appointment = MagicMock(id=82, loja_id=6)
        appointment.date = timezone.make_aware(datetime(2026, 9, 22, 16, 45))
        mock_envio.objects.filter.return_value.exists.return_value = False
        mock_config.objects.filter.return_value.first.return_value = _config_ok()

        with patch(
            "whatsapp.confirmacao_agenda_service.dias_ate_consulta",
            return_value=7,
        ):
            _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_envio.objects.filter.assert_any_call(appointment_id=82)
        mock_agendar.assert_not_called()

    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.confirmacao_agenda_service.antecedencias_da_config", return_value=[1])
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_nao_envia_ao_corrigir_no_dia_da_regra_se_ainda_nao_tinha_ido(
        self, mock_envio, mock_config, _antec, mock_agendar,
    ):
        appointment = MagicMock(id=82, loja_id=6)
        mock_envio.objects.filter.return_value.exists.return_value = False
        mock_config.objects.filter.return_value.first.return_value = _config_ok()

        with patch("whatsapp.confirmacao_agenda_service.dias_ate_consulta", return_value=1):
            _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_agendar.assert_not_called()

    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.confirmacao_agenda_service.antecedencias_da_config", return_value=[1])
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_avisa_se_cliente_ja_tinha_o_link_e_consulta_e_hoje(
        self, mock_envio, mock_config, _antec, mock_agendar,
    ):
        appointment = MagicMock(id=82, loja_id=6)
        mock_envio.objects.filter.return_value.exists.return_value = True
        mock_config.objects.filter.return_value.first.return_value = _config_ok()

        with patch("whatsapp.confirmacao_agenda_service.dias_ate_consulta", return_value=0):
            _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_agendar.assert_called_once_with(82, 6)

    @patch("whatsapp.services.enviar_confirmacao_agendamento")
    @patch("clinica_beleza.agenda_service._agendar_confirmacao_reagendamento")
    @patch("whatsapp.confirmacao_agenda_service.antecedencias_da_config", return_value=[1])
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("whatsapp.models.WhatsAppConfirmacaoEnvio")
    def test_nao_chama_evolution_no_request(
        self, mock_envio, mock_config, _antec, mock_agendar, mock_enviar,
    ):
        appointment = MagicMock(id=82, loja_id=6)
        mock_envio.objects.filter.return_value.exists.return_value = False
        mock_config.objects.filter.return_value.first.return_value = _config_ok()

        with patch("whatsapp.confirmacao_agenda_service.dias_ate_consulta", return_value=1):
            _redisparar_confirmacao_por_mudanca_data(appointment)

        mock_enviar.assert_not_called()
        mock_agendar.assert_not_called()


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
