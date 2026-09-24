from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import AgendaValidationError
from clinica_beleza.protocolo_comercial import (
    classificar_selecao_protocolo,
    datas_das_sessoes,
    dividir_valor_protocolo,
)


class DividirValorProtocoloTests(SimpleTestCase):
    def test_por_consulta_divide_igual(self):
        partes = dividir_valor_protocolo(Decimal("1200"), 4, "POR_CONSULTA")
        self.assertEqual(partes, [Decimal("300.00")] * 4)

    def test_centavos_ficam_na_ultima_sessao(self):
        partes = dividir_valor_protocolo(Decimal("1000"), 3, "POR_CONSULTA")
        self.assertEqual(partes, [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")])

    def test_valor_total_cobra_so_a_primeira(self):
        partes = dividir_valor_protocolo(Decimal("1200"), 4, "TOTAL")
        self.assertEqual(
            partes,
            [Decimal("1200.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        )


class ClassificarSelecaoProtocoloTests(SimpleTestCase):
    def test_procedimento_comum_segue_agendamento_normal(self):
        proc = SimpleNamespace(id=1, categoria="facial")
        self.assertIsNone(classificar_selecao_protocolo([proc], []))

    def test_protocolo_unico_e_agendado(self):
        proc = SimpleNamespace(id=4, categoria="protocolo")
        proto = SimpleNamespace(procedure_id=4)
        self.assertIs(classificar_selecao_protocolo([proc], [proto]), proto)

    def test_categoria_sem_cadastro_pede_o_protocolo(self):
        proc = SimpleNamespace(id=4, categoria="protocolo")
        with self.assertRaisesMessage(
            AgendaValidationError,
            "Cadastre o protocolo deste procedimento em Protocolos antes de agendar.",
        ):
            classificar_selecao_protocolo([proc], [])

    def test_mistura_com_outro_procedimento_e_recusada(self):
        procedimentos = [
            SimpleNamespace(id=4, categoria="protocolo"),
            SimpleNamespace(id=5, categoria="facial"),
        ]
        proto = SimpleNamespace(procedure_id=4)
        with self.assertRaisesMessage(AgendaValidationError, "O protocolo é agendado sozinho."):
            classificar_selecao_protocolo(procedimentos, [proto])


class DatasSessoesTests(SimpleTestCase):
    def test_quatro_sessoes_a_cada_sete_dias_duram_vinte_e_um_dias(self):
        inicio = datetime(2026, 9, 24, 15, 0)
        datas = datas_das_sessoes(inicio, 4, 7, "dias")
        self.assertEqual(datas[0], inicio)
        self.assertEqual(datas[3], datetime(2026, 10, 15, 15, 0))
        self.assertEqual((datas[3] - datas[0]).days, 21)

    def test_intervalo_em_semanas(self):
        inicio = datetime(2026, 9, 24, 15, 0)
        datas = datas_das_sessoes(inicio, 4, 1, "semanas")
        self.assertEqual(datas[1], datetime(2026, 10, 1, 15, 0))

    def test_intervalo_em_meses_no_fim_do_mes(self):
        inicio = datetime(2026, 1, 31, 10, 0)
        datas = datas_das_sessoes(inicio, 2, 1, "meses")
        self.assertEqual(datas[1], datetime(2026, 2, 28, 10, 0))
