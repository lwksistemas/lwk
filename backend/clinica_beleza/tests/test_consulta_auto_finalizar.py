"""Testes da auto-finalização de consultas esquecidas."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.consulta_auto_finalizar_service import (
    INATIVIDADE_MINIMA_HORAS,
    MARGEM_COM_PROCEDIMENTO_HORAS,
    _horario_limite_finalizacao,
)


class HorarioLimiteAutoFinalizarTest(SimpleTestCase):
    def test_limite_com_procedimento_usa_margem_longa(self):
        inicio = timezone.now()
        appointment = MagicMock()
        appointment.get_duracao_efetiva.return_value = 60
        appointment.appointment_procedures.exists.return_value = True
        appointment.procedure_id = 1
        consulta = MagicMock(data_inicio=inicio, appointment=appointment)

        limite = _horario_limite_finalizacao(consulta)

        self.assertEqual(
            limite,
            inicio + timedelta(minutes=60, hours=MARGEM_COM_PROCEDIMENTO_HORAS),
        )

    def test_inatividade_minima_configurada(self):
        self.assertGreaterEqual(INATIVIDADE_MINIMA_HORAS, 3)
