"""Fila da página Consultas: cliente presente e em atendimento."""
from django.db.models import Q
from django.test import SimpleTestCase

from clinica_beleza.views_consultas.helpers import q_consultas_aguardando_inicio


class FilaConsultasAguardandoInicioTest(SimpleTestCase):
    def test_q_tem_presente_e_em_atendimento(self):
        q = q_consultas_aguardando_inicio()
        self.assertEqual(len(q.children), 2)
        self.assertEqual(q.connector, "OR")

    def test_q_inclui_receber_com_agenda_em_atendimento(self):
        """Corrigir pagamento no meio do atendimento não pode tirar da fila."""
        expected = (
            Q(
                status__in=("SCHEDULED", "RECEBER"),
                appointment__status__in=("CONFIRMED", "IN_PROGRESS"),
            )
            | Q(status="IN_PROGRESS")
        )
        self.assertEqual(q_consultas_aguardando_inicio(), expected)
