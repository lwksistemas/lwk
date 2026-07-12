"""Testes — regra de uma consulta em andamento por paciente."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_service import (
    MSG_PACIENTE_CONSULTA_EM_ANDAMENTO,
    iniciar_consulta,
    validar_paciente_sem_consulta_em_andamento,
)


class ValidarPacienteSemConsultaEmAndamentoTest(SimpleTestCase):
    @patch('clinica_beleza.consulta_service.Consulta')
    def test_bloqueia_quando_ja_existe_em_andamento(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value.exclude.return_value.exists.return_value = True
        with self.assertRaisesMessage(ValueError, MSG_PACIENTE_CONSULTA_EM_ANDAMENTO):
            validar_paciente_sem_consulta_em_andamento(1, exclude_consulta_id=2)

    @patch('clinica_beleza.consulta_service.Consulta')
    def test_permite_quando_nao_ha_outra_em_andamento(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value.exclude.return_value.exists.return_value = False
        validar_paciente_sem_consulta_em_andamento(1, exclude_consulta_id=2)


class IniciarConsultaPacienteEmAndamentoTest(SimpleTestCase):
    @patch('clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento')
    @patch('clinica_beleza.consulta_service.sync_consulta_from_appointment_status')
    def test_iniciar_chama_validacao_do_paciente(self, _mock_sync, mock_validar):
        consulta = MagicMock()
        consulta.status = 'SCHEDULED'
        consulta.patient_id = 10
        consulta.id = 4
        consulta.appointment = MagicMock(status='CONFIRMED')

        iniciar_consulta(consulta)

        mock_validar.assert_called_once_with(10, exclude_consulta_id=4)

    @patch('clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento')
    @patch('clinica_beleza.consulta_service.sync_consulta_from_appointment_status')
    def test_iniciar_aceita_status_receber(self, _mock_sync, mock_validar):
        consulta = MagicMock()
        consulta.status = 'RECEBER'
        consulta.patient_id = 10
        consulta.id = 4
        consulta.appointment = MagicMock(status='CONFIRMED')

        iniciar_consulta(consulta)

        mock_validar.assert_called_once_with(10, exclude_consulta_id=4)
        self.assertEqual(consulta.status, 'IN_PROGRESS')

    @patch('clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento')
    @patch('clinica_beleza.consulta_service.sync_consulta_from_appointment_status')
    @patch('clinica_beleza.consulta_service.lifecycle.now')
    def test_iniciar_atualiza_data_hora_agendamento(self, mock_now, _mock_sync, _mock_validar):
        from django.utils.timezone import datetime
        ts = datetime(2026, 7, 20, 14, 30)
        mock_now.return_value = ts
        appointment = MagicMock(status='CONFIRMED')
        consulta = MagicMock()
        consulta.status = 'SCHEDULED'
        consulta.patient_id = 10
        consulta.id = 4
        consulta.appointment = appointment

        iniciar_consulta(consulta)

        self.assertEqual(appointment.date, ts)
        self.assertEqual(consulta.data_inicio, ts)
