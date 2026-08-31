"""Fila da página Consultas: cliente presente e em atendimento."""
from django.test import SimpleTestCase

from clinica_beleza.views_consultas.helpers import q_consultas_aguardando_inicio


class FilaConsultasAguardandoInicioTest(SimpleTestCase):
    def test_q_tem_presente_e_em_atendimento(self):
        q = q_consultas_aguardando_inicio()
        self.assertEqual(len(q.children), 2)
        connector = q.connector
        self.assertEqual(connector, "OR")
