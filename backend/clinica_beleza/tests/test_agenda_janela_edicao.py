"""Agendamento vencido ainda pode ser alterado por 2 dias; finalizada só a data."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.agenda_service import (
    AgendaValidationError,
    MSG_FINALIZADA_SO_DATA,
    atualizar_agendamento,
    horario_agendamento_passou,
)


class HorarioAgendamentoPassouTest(SimpleTestCase):
    @patch("clinica_beleza.agenda_service.now")
    def test_dentro_de_2_dias_ainda_libera_edicao(self, mock_now):
        agora = timezone.now()
        mock_now.return_value = agora
        appointment = MagicMock(date=agora - timedelta(days=1, hours=23))
        self.assertFalse(horario_agendamento_passou(appointment))

    @patch("clinica_beleza.agenda_service.now")
    def test_depois_de_2_dias_trava(self, mock_now):
        agora = timezone.now()
        mock_now.return_value = agora
        appointment = MagicMock(date=agora - timedelta(days=2, minutes=1))
        self.assertTrue(horario_agendamento_passou(appointment))


class FinalizadaPermiteSoDataTest(SimpleTestCase):
    def _appointment_finalizado(self, agora):
        appointment = MagicMock()
        appointment.status = "COMPLETED"
        appointment.date = agora - timedelta(hours=3)
        appointment.professional_id = 1
        appointment.duracao_minutos = 30
        appointment.version = 1
        appointment.confirmacao_generation = 1
        appointment.get_duracao_efetiva.return_value = 30
        appointment.appointment_procedures.order_by.return_value.values_list.return_value = []
        appointment.procedure_id = None
        return appointment

    @patch("clinica_beleza.agenda_service._sincronizar_horario_consulta_finalizada")
    @patch("clinica_beleza.agenda_service.validar_regras_agendamento")
    @patch("clinica_beleza.agenda_service.bloqueio_impede_agendamento", return_value=False)
    @patch("clinica_beleza.agenda_service.horario_agendamento_passou", return_value=False)
    def test_finalizada_pode_mudar_data(self, _passou, _bloq, _regras, mock_sync):
        agora = timezone.now()
        appointment = self._appointment_finalizado(agora)
        nova = agora - timedelta(hours=5)

        result = atualizar_agendamento(appointment, new_date=nova)

        self.assertEqual(appointment.date, nova)
        appointment.save.assert_called()
        mock_sync.assert_called_once()
        self.assertIs(result.appointment, appointment)

    @patch("clinica_beleza.agenda_service.horario_agendamento_passou", return_value=False)
    def test_finalizada_nao_pode_mudar_profissional(self, _passou):
        agora = timezone.now()
        appointment = self._appointment_finalizado(agora)

        with self.assertRaisesMessage(AgendaValidationError, MSG_FINALIZADA_SO_DATA):
            atualizar_agendamento(appointment, new_professional=9)
