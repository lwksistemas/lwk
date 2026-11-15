import unittest
from datetime import datetime, timedelta

from salao_cabeleireiro.agenda_service import intervalos_conflitam
from salao_cabeleireiro.serializers import painel_valido


class IntervaloAgendaTest(unittest.TestCase):
    def test_horario_seguido_nao_conflita(self):
        inicio = datetime(2026, 11, 14, 10, 0)
        meio = inicio + timedelta(hours=1)
        fim = inicio + timedelta(hours=2)
        self.assertFalse(intervalos_conflitam(inicio, meio, meio, fim))

    def test_horario_sobreposto_conflita(self):
        inicio = datetime(2026, 11, 14, 10, 0)
        self.assertTrue(
            intervalos_conflitam(
                inicio,
                inicio + timedelta(hours=1),
                inicio + timedelta(minutes=30),
                inicio + timedelta(hours=2),
            )
        )


class PainelSalaoTest(unittest.TestCase):
    def test_so_os_tres_paineis(self):
        self.assertTrue(painel_valido("operacao"))
        self.assertTrue(painel_valido("gestao"))
        self.assertTrue(painel_valido("semana"))
        self.assertFalse(painel_valido("outro"))
