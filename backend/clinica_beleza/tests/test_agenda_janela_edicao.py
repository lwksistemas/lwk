"""Agendamento vencido ainda pode ser alterado por 2 dias."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.agenda_service import horario_agendamento_passou


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
