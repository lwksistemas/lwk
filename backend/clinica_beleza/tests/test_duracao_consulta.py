from types import SimpleNamespace
from unittest import TestCase

from clinica_beleza.duracao_consulta import (
    calcular_duracao_efetiva_agendamento,
    calcular_duracao_novo_agendamento,
    tempo_consulta_base_minutos,
)


class DuracaoConsultaTests(TestCase):
    def test_base_usa_local(self):
        local = SimpleNamespace(tempo_consulta_minutos=40)
        self.assertEqual(tempo_consulta_base_minutos(local_atendimento=local), 40)

    def test_base_padrao_30_min(self):
        self.assertEqual(tempo_consulta_base_minutos(), 30)

    def test_procedimentos_maiores_prevalecem(self):
        local = SimpleNamespace(tempo_consulta_minutos=30)
        proc_a = SimpleNamespace(duracao_minutos=20)
        proc_b = SimpleNamespace(duracao_minutos=25)
        total = calcular_duracao_novo_agendamento(
            professional=None,
            local_atendimento=local,
            procedures_list=[proc_a, proc_b],
        )
        self.assertEqual(total, 45)

    def test_tempo_local_maior_que_procedimentos(self):
        local = SimpleNamespace(tempo_consulta_minutos=60)
        proc = SimpleNamespace(duracao_minutos=30)
        total = calcular_duracao_novo_agendamento(
            professional=None,
            local_atendimento=local,
            procedures_list=[proc],
        )
        self.assertEqual(total, 60)

    def test_sem_procedimentos_usa_local(self):
        local = SimpleNamespace(tempo_consulta_minutos=50)
        total = calcular_duracao_novo_agendamento(
            professional=None,
            local_atendimento=local,
        )
        self.assertEqual(total, 50)

    def test_duracao_manual_prevalece(self):
        local = SimpleNamespace(tempo_consulta_minutos=30)
        proc = SimpleNamespace(duracao_minutos=20, get_duracao=lambda: 20)
        total = calcular_duracao_efetiva_agendamento(
            duracao_manual=90,
            professional=None,
            local_atendimento=local,
            appointment_procedures=[proc],
        )
        self.assertEqual(total, 90)
