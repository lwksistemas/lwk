"""Testes do valor exibido na agenda (consulta + procedimentos)."""
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase

from clinica_beleza.models.appointments import calcular_valor_exibicao_agenda


class AgendaValorExibicaoTests(TestCase):
    def test_consulta_pura_com_local(self):
        local = SimpleNamespace(valor_consulta=Decimal("150.00"))
        valor = calcular_valor_exibicao_agenda(
            Decimal(0),
            local_atendimento=local,
        )
        self.assertEqual(valor, Decimal("150.00"))

    def test_local_mais_procedimentos(self):
        local = SimpleNamespace(valor_consulta=Decimal("100.00"))
        valor = calcular_valor_exibicao_agenda(
            Decimal("250.00"),
            local_atendimento=local,
        )
        self.assertEqual(valor, Decimal("350.00"))

    def test_somente_procedimentos_sem_local(self):
        valor = calcular_valor_exibicao_agenda(Decimal("80.00"))
        self.assertEqual(valor, Decimal("80.00"))

    def test_legacy_procedure_sem_local(self):
        proc = SimpleNamespace(preco=Decimal("120.00"))
        valor = calcular_valor_exibicao_agenda(
            Decimal(0),
            procedure=proc,
            procedure_id=1,
        )
        self.assertEqual(valor, Decimal("120.00"))

    def test_fallback_valor_consulta_vinculada(self):
        consulta = SimpleNamespace(valor_consulta=Decimal("90.00"))
        valor = calcular_valor_exibicao_agenda(
            Decimal(0),
            consulta=consulta,
        )
        self.assertEqual(valor, Decimal("90.00"))

    def test_retorno_gratuito_zera_taxa_local(self):
        local = SimpleNamespace(valor_consulta=Decimal("150.00"))
        consulta = SimpleNamespace(valor_consulta=Decimal("150.00"), retorno_gratuito=True)
        valor = calcular_valor_exibicao_agenda(
            Decimal("50.00"),
            local_atendimento=local,
            consulta=consulta,
        )
        self.assertEqual(valor, Decimal("50.00"))

    def test_retorno_gratuito_sem_local_zera_taxa(self):
        consulta = SimpleNamespace(valor_consulta=Decimal("90.00"), retorno_gratuito=True)
        valor = calcular_valor_exibicao_agenda(Decimal(0), consulta=consulta)
        self.assertEqual(valor, Decimal(0))
