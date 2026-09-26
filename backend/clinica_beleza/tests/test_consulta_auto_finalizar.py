"""Testes da auto-finalização de consultas esquecidas."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.consulta_auto_finalizar_service import (
    MARGEM_APOS_FIM_AGENDAMENTO_HORAS,
    _finalizar_cliente_presente_sem_iniciar,
    _fim_agendamento,
    _horario_limite_finalizacao,
)


class HorarioLimiteAutoFinalizarTest(SimpleTestCase):
    def test_cinco_horas_apos_fim_do_agendamento(self):
        inicio = timezone.now()
        appointment = MagicMock()
        appointment.date = inicio
        appointment.get_duracao_efetiva.return_value = 40
        consulta = MagicMock(data_inicio=inicio, appointment=appointment)

        limite = _horario_limite_finalizacao(consulta=consulta)

        self.assertEqual(
            limite,
            inicio + timedelta(minutes=40, hours=MARGEM_APOS_FIM_AGENDAMENTO_HORAS),
        )
        self.assertEqual(MARGEM_APOS_FIM_AGENDAMENTO_HORAS, 5)

    def test_usa_data_inicio_se_appointment_sem_data(self):
        inicio = timezone.now()
        appointment = MagicMock()
        appointment.date = None
        appointment.get_duracao_efetiva.return_value = 30
        consulta = MagicMock(data_inicio=inicio, appointment=appointment)

        self.assertEqual(_fim_agendamento(consulta=consulta), inicio + timedelta(minutes=30))

    def test_sem_inicio_nao_tem_limite(self):
        appointment = MagicMock()
        appointment.date = None
        consulta = MagicMock(data_inicio=None, appointment=appointment)
        self.assertIsNone(_horario_limite_finalizacao(consulta=consulta))

    def test_limite_pelo_appointment_sem_consulta(self):
        inicio = timezone.now()
        appointment = MagicMock()
        appointment.date = inicio
        appointment.get_duracao_efetiva.return_value = 60
        limite = _horario_limite_finalizacao(appointment=appointment)
        self.assertEqual(
            limite,
            inicio + timedelta(minutes=60, hours=MARGEM_APOS_FIM_AGENDAMENTO_HORAS),
        )


def _qs_appointments(itens):
    qs = MagicMock()
    qs.select_related.return_value = qs
    qs.prefetch_related.return_value = qs
    qs.order_by.return_value = qs
    qs.iterator.return_value = iter(itens)
    return qs


class ClientePresenteSemIniciarTest(SimpleTestCase):
    @patch("clinica_beleza.consulta_auto_finalizar_service._finalizar_com_horario_agendado")
    @patch("clinica_beleza.consulta_auto_finalizar_service._garantir_consulta_cliente_presente")
    def test_finaliza_cliente_presente_apos_margem(self, mock_garantir, mock_fin):
        agora = timezone.now()
        inicio = agora - timedelta(hours=7)
        appointment = MagicMock(
            id=10,
            status="CONFIRMED",
            date=inicio,
            patient_id=1,
            patient=MagicMock(nome="Paciente"),
        )
        appointment.get_duracao_efetiva.return_value = 30
        consulta = MagicMock(id=20, status="RECEBER")
        consulta.refresh_from_db = MagicMock()
        mock_garantir.return_value = consulta

        with patch("clinica_beleza.models.Appointment") as Appt:
            Appt.objects.filter.return_value = _qs_appointments([appointment])
            total = _finalizar_cliente_presente_sem_iniciar(agora)

        self.assertEqual(total, 1)
        mock_fin.assert_called_once_with(consulta)

    @patch("clinica_beleza.consulta_auto_finalizar_service._finalizar_com_horario_agendado")
    def test_nao_finaliza_antes_da_margem(self, mock_fin):
        agora = timezone.now()
        inicio = agora - timedelta(hours=1)
        appointment = MagicMock(id=11, status="CONFIRMED", date=inicio, patient_id=1)
        appointment.get_duracao_efetiva.return_value = 30

        with patch("clinica_beleza.models.Appointment") as Appt:
            Appt.objects.filter.return_value = _qs_appointments([appointment])
            total = _finalizar_cliente_presente_sem_iniciar(agora)

        self.assertEqual(total, 0)
        mock_fin.assert_not_called()

    @patch("clinica_beleza.consulta_auto_finalizar_service._finalizar_com_horario_agendado")
    @patch("clinica_beleza.consulta_auto_finalizar_service._garantir_consulta_cliente_presente")
    def test_ignora_consulta_ja_em_andamento(self, mock_garantir, mock_fin):
        agora = timezone.now()
        inicio = agora - timedelta(hours=7)
        appointment = MagicMock(
            id=12, status="CONFIRMED", date=inicio, patient_id=1, patient=MagicMock(nome="X"),
        )
        appointment.get_duracao_efetiva.return_value = 30
        consulta = MagicMock(id=21, status="IN_PROGRESS")
        consulta.refresh_from_db = MagicMock()
        mock_garantir.return_value = consulta

        with patch("clinica_beleza.models.Appointment") as Appt:
            Appt.objects.filter.return_value = _qs_appointments([appointment])
            total = _finalizar_cliente_presente_sem_iniciar(agora)

        self.assertEqual(total, 0)
        mock_fin.assert_not_called()
