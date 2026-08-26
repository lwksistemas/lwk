from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import (
    AgendaValidationError,
    _profissional_ativo,
    atualizar_agendamento,
)


class ProfissionalAtivoTest(SimpleTestCase):
    def test_id_invalido(self):
        with self.assertRaises(AgendaValidationError):
            _profissional_ativo("abc")

    @patch("clinica_beleza.agenda_service.Professional.objects")
    def test_nao_encontrado(self, mock_objects):
        mock_objects.filter.return_value.first.return_value = None
        with self.assertRaises(AgendaValidationError):
            _profissional_ativo(99)


class AtualizarAgendamentoProfissionalTest(SimpleTestCase):
    @patch("clinica_beleza.agenda_service._redisparar_confirmacao_por_mudanca_data")
    @patch("clinica_beleza.agenda_service._sync_consulta_profissional")
    @patch("clinica_beleza.agenda_service.validar_regras_agendamento")
    @patch("clinica_beleza.agenda_service.bloqueio_impede_agendamento", return_value=False)
    @patch("clinica_beleza.agenda_service._profissional_ativo")
    def test_troca_profissional_e_dispara_whatsapp(
        self, mock_prof, _bloq, _regras, mock_sync, mock_whats,
    ):
        novo = MagicMock(id=7)
        mock_prof.return_value = novo
        appointment = MagicMock(
            id=10,
            professional_id=3,
            date=datetime(2026, 8, 26, 8, 10),
            status="SCHEDULED",
            version=1,
        )
        appointment.get_duracao_efetiva.return_value = 40

        atualizar_agendamento(appointment, new_professional=7, user=None)

        self.assertEqual(appointment.professional, novo)
        appointment.save.assert_called_once()
        mock_sync.assert_called_once_with(appointment, novo)
        mock_whats.assert_called_once_with(appointment)

    @patch("clinica_beleza.agenda_service._redisparar_confirmacao_por_mudanca_data")
    @patch("clinica_beleza.agenda_service.validar_regras_agendamento")
    @patch("clinica_beleza.agenda_service.bloqueio_impede_agendamento", return_value=False)
    @patch("clinica_beleza.agenda_service._profissional_ativo")
    def test_mesmo_profissional_nao_troca(self, mock_prof, _bloq, _regras, mock_whats):
        atual = MagicMock(id=3)
        mock_prof.return_value = atual
        appointment = MagicMock(
            id=10,
            professional_id=3,
            date=datetime(2026, 8, 26, 8, 10),
            status="SCHEDULED",
            version=1,
        )
        appointment.get_duracao_efetiva.return_value = 40

        atualizar_agendamento(appointment, new_professional=3, user=None)

        mock_whats.assert_not_called()
