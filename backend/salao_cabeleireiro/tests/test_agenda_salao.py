import unittest
from datetime import datetime, time, timedelta

from salao_cabeleireiro.agenda_service import avaliar_jornada, intervalos_conflitam
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


class JornadaAgendaTest(unittest.TestCase):
    def test_dentro_do_expediente(self):
        self.assertIsNone(avaliar_jornada(time(9, 0), time(19, 0), None, None, time(10, 0), time(11, 0)))

    def test_antes_da_entrada(self):
        self.assertIn("fora da jornada", avaliar_jornada(time(9, 0), time(19, 0), None, None, time(8, 0), time(9, 30)))

    def test_em_cima_do_intervalo(self):
        self.assertIn("intervalo", avaliar_jornada(time(9, 0), time(19, 0), time(12, 0), time(13, 0), time(12, 30), time(13, 30)))

    def test_intervalo_nao_bloqueia_o_horario_seguinte(self):
        self.assertIsNone(avaliar_jornada(time(9, 0), time(19, 0), time(12, 0), time(13, 0), time(13, 0), time(14, 0)))


class PainelSalaoTest(unittest.TestCase):
    def test_so_os_tres_paineis(self):
        self.assertTrue(painel_valido("operacao"))
        self.assertTrue(painel_valido("gestao"))
        self.assertTrue(painel_valido("semana"))
        self.assertFalse(painel_valido("outro"))
