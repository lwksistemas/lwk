"""Nome do procedimento no financeiro inclui o retorno sem cobrança."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.serializers.financeiro import _procedimentos_nome_agendamento


class ProcedimentosNomeAgendamentoTest(SimpleTestCase):
    def test_retorno_sem_procedimento_cobrado_mostra_o_nome(self):
        appointment = SimpleNamespace(
            _prefetched_objects_cache={"appointment_procedures": []},
            procedure_id=None,
            procedure=None,
            retorno_procedure=SimpleNamespace(nome="LASER ETHEREA"),
            consulta=None,
        )
        self.assertEqual(_procedimentos_nome_agendamento(appointment), "LASER ETHEREA")

    def test_evolucao_quando_nao_ha_procedimento(self):
        appointment = SimpleNamespace(
            _prefetched_objects_cache={"appointment_procedures": []},
            procedure_id=None,
            procedure=None,
            retorno_procedure=None,
            consulta=SimpleNamespace(
                evolucoes_recentes=[SimpleNamespace(procedimento_realizado="Laser facial")],
            ),
        )
        self.assertEqual(_procedimentos_nome_agendamento(appointment), "Laser facial")
