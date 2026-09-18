"""Testes — regras ao iniciar consulta (paciente e profissional/local)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_service import (
    MSG_PACIENTE_CONSULTA_EM_ANDAMENTO,
    MSG_PROFISSIONAL_LOCAL_EM_ANDAMENTO,
    iniciar_consulta,
    local_id_efetivo_consulta,
    validar_paciente_sem_consulta_em_andamento,
    validar_profissional_livre_no_local,
)


def _qs_exists(exists):
    qs = MagicMock()
    qs.annotate.return_value = qs
    qs.filter.return_value = qs
    qs.exclude.return_value = qs
    qs.exists.return_value = exists
    return qs


class ValidarPacienteSemConsultaEmAndamentoTest(SimpleTestCase):
    @patch("clinica_beleza.consulta_service.Consulta")
    def test_bloqueia_quando_ja_existe_em_andamento(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value.exclude.return_value.exists.return_value = True
        with self.assertRaisesMessage(ValueError, MSG_PACIENTE_CONSULTA_EM_ANDAMENTO):
            validar_paciente_sem_consulta_em_andamento(1, exclude_consulta_id=2)

    @patch("clinica_beleza.consulta_service.Consulta")
    def test_permite_quando_nao_ha_outra_em_andamento(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value.exclude.return_value.exists.return_value = False
        validar_paciente_sem_consulta_em_andamento(1, exclude_consulta_id=2)


class ValidarProfissionalLivreNoLocalTest(SimpleTestCase):
    @patch("clinica_beleza.consulta_service.Consulta")
    def test_bloqueia_mesmo_profissional_mesmo_local(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value = _qs_exists(True)
        with self.assertRaisesMessage(ValueError, MSG_PROFISSIONAL_LOCAL_EM_ANDAMENTO):
            validar_profissional_livre_no_local(9, 3, exclude_consulta_id=1)

    @patch("clinica_beleza.consulta_service.Consulta")
    def test_permite_outro_local(self, mock_consulta_model):
        mock_consulta_model.objects.filter.return_value = _qs_exists(False)
        validar_profissional_livre_no_local(9, 7, exclude_consulta_id=1)

    def test_sem_profissional_nao_bloqueia(self):
        validar_profissional_livre_no_local(None, 3)

    def test_local_efetivo_usa_consulta_depois_agenda(self):
        consulta = MagicMock(local_atendimento_id=5)
        consulta.appointment.local_atendimento_id = 8
        self.assertEqual(local_id_efetivo_consulta(consulta), 5)
        consulta.local_atendimento_id = None
        self.assertEqual(local_id_efetivo_consulta(consulta), 8)


class IniciarConsultaPacienteEmAndamentoTest(SimpleTestCase):
    @patch("clinica_beleza.consulta_service.validar_profissional_livre_no_local")
    @patch("clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento")
    @patch("clinica_beleza.consulta_service.sync_consulta_from_appointment_status")
    def test_iniciar_chama_validacao_do_paciente(self, _mock_sync, mock_validar, mock_local):
        consulta = MagicMock()
        consulta.status = "SCHEDULED"
        consulta.patient_id = 10
        consulta.professional_id = 9
        consulta.local_atendimento_id = 3
        consulta.id = 4
        consulta.appointment = MagicMock(status="CONFIRMED", professional_id=9, local_atendimento_id=3)

        iniciar_consulta(consulta)

        mock_validar.assert_called_once_with(10, exclude_consulta_id=4)
        mock_local.assert_called_once_with(9, 3, exclude_consulta_id=4)

    @patch("clinica_beleza.consulta_service.validar_profissional_livre_no_local")
    @patch("clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento")
    @patch("clinica_beleza.consulta_service.sync_consulta_from_appointment_status")
    def test_iniciar_aceita_status_receber(self, _mock_sync, mock_validar, _mock_local):
        consulta = MagicMock()
        consulta.status = "RECEBER"
        consulta.patient_id = 10
        consulta.professional_id = 9
        consulta.local_atendimento_id = None
        consulta.id = 4
        consulta.appointment = MagicMock(status="CONFIRMED", professional_id=9, local_atendimento_id=2)

        iniciar_consulta(consulta)

        mock_validar.assert_called_once_with(10, exclude_consulta_id=4)
        self.assertEqual(consulta.status, "IN_PROGRESS")

    @patch("clinica_beleza.consulta_service.validar_profissional_livre_no_local")
    @patch("clinica_beleza.consulta_service.validar_paciente_sem_consulta_em_andamento")
    @patch("clinica_beleza.consulta_service.sync_consulta_from_appointment_status")
    @patch("clinica_beleza.consulta_service.lifecycle.now")
    def test_iniciar_atualiza_data_hora_agendamento(self, mock_now, _mock_sync, _mock_validar, _mock_local):
        from django.utils.timezone import datetime
        ts = datetime(2026, 7, 20, 14, 30)
        mock_now.return_value = ts
        appointment = MagicMock(status="CONFIRMED", professional_id=9, local_atendimento_id=1)
        consulta = MagicMock()
        consulta.status = "SCHEDULED"
        consulta.patient_id = 10
        consulta.professional_id = 9
        consulta.local_atendimento_id = 1
        consulta.id = 4
        consulta.appointment = appointment

        iniciar_consulta(consulta)

        self.assertEqual(appointment.date, ts)
        self.assertEqual(consulta.data_inicio, ts)
