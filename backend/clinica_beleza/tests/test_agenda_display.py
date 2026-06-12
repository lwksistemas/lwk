"""Testes de exibição de data/hora de agendamentos."""
from datetime import datetime, timezone as dt_timezone
from unittest import TestCase
from unittest.mock import patch

from clinica_beleza.agenda_display import format_agenda_data, format_agenda_hora


class AgendaDisplayTest(TestCase):
    @patch('clinica_beleza.agenda_display.timezone.localtime')
    def test_format_usa_fuso_local(self, mock_localtime):
        utc = datetime(2026, 6, 16, 18, 5, tzinfo=dt_timezone.utc)
        mock_localtime.return_value = datetime(2026, 6, 16, 15, 5)

        self.assertEqual(format_agenda_data(utc), '16/06/2026')
        self.assertEqual(format_agenda_hora(utc), '15:05')
