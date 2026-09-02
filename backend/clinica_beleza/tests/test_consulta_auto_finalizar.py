"""Testes da auto-finalização de consultas esquecidas."""
from datetime import timedelta
from unittest.mock import MagicMock

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.consulta_auto_finalizar_service import (
    MARGEM_APOS_FIM_AGENDAMENTO_HORAS,
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

        limite = _horario_limite_finalizacao(consulta)

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

        self.assertEqual(_fim_agendamento(consulta), inicio + timedelta(minutes=30))

    def test_sem_inicio_nao_tem_limite(self):
        appointment = MagicMock()
        appointment.date = None
        consulta = MagicMock(data_inicio=None, appointment=appointment)
        self.assertIsNone(_horario_limite_finalizacao(consulta))
