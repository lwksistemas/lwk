"""Testes de agregação financeira (performance — sem N+1)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class TestPaymentsVisiveisFinanceiro(SimpleTestCase):
    def test_agendamento_cancelado_fica_fora_da_listagem(self):
        from clinica_beleza.financeiro_service import payments_visiveis_financeiro

        qs = MagicMock()
        qs.exclude.return_value = qs
        qs.filter.return_value = qs
        payments_visiveis_financeiro(qs)
        qs.exclude.assert_any_call(status="DRAFT")
        qs.exclude.assert_any_call(appointment__status="CANCELLED")


class TestSomarContasAReceber(SimpleTestCase):
    def test_usa_agregacao_sem_iterar_payments(self):
        from clinica_beleza.financeiro_service import somar_contas_a_receber

        mock_qs = MagicMock()
        chain = mock_qs.filter.return_value
        chain.annotate.return_value.annotate.return_value.annotate.return_value.aggregate.return_value = {
            "t": 150.5,
        }

        with patch("clinica_beleza.financeiro_service.payments_visiveis_financeiro", return_value=mock_qs), patch(
            "clinica_beleza.financeiro_service.PaymentParcela",
        ):
            total = somar_contas_a_receber()
        self.assertEqual(total, 150.5)
        mock_qs.filter.assert_called()


class TestNomeProcedimentoPayment(SimpleTestCase):
    def test_prefere_linhas_do_agendamento(self):
        from clinica_beleza.financeiro_service import _nome_procedimento_payment

        proc = SimpleNamespace(nome="DRENAGEM")
        linha = SimpleNamespace(procedure=proc)
        appt = SimpleNamespace(
            _prefetched_objects_cache={"appointment_procedures": [linha]},
            procedure=SimpleNamespace(nome="LEGADO"),
        )
        payment = SimpleNamespace(appointment=appt)
        self.assertEqual(_nome_procedimento_payment(payment), "DRENAGEM")

    def test_cai_no_procedimento_legado(self):
        from clinica_beleza.financeiro_service import _nome_procedimento_payment

        appt = SimpleNamespace(
            _prefetched_objects_cache={},
            procedure=SimpleNamespace(nome="CONSULTA"),
        )
        self.assertEqual(_nome_procedimento_payment(SimpleNamespace(appointment=appt)), "CONSULTA")


class TestErroExcluirPayment(SimpleTestCase):
    def test_bloqueia_pago_e_parcial(self):
        from clinica_beleza.financeiro_service import erro_excluir_payment

        for status in ("PAID", "PARTIAL"):
            payment = SimpleNamespace(status=status, parcelas=MagicMock())
            self.assertIsNotNone(erro_excluir_payment(payment))

    def test_bloqueia_se_tem_parcela_paga(self):
        from clinica_beleza.financeiro_service import erro_excluir_payment

        parcelas = MagicMock()
        parcelas.filter.return_value.exists.return_value = True
        payment = SimpleNamespace(status="PENDING", parcelas=parcelas)
        self.assertIsNotNone(erro_excluir_payment(payment))

    def test_permite_pendente_sem_parcela(self):
        from clinica_beleza.financeiro_service import erro_excluir_payment

        parcelas = MagicMock()
        parcelas.filter.return_value.exists.return_value = False
        payment = SimpleNamespace(status="PENDING", parcelas=parcelas)
        self.assertIsNone(erro_excluir_payment(payment))


class TestResumoSeparaPrazo(SimpleTestCase):
    def test_a_receber_do_mes_nao_repete_o_prazo(self):
        from datetime import date

        from clinica_beleza.financeiro_service import montar_resumo_financeiro

        qs = MagicMock()
        qs.exclude.return_value = qs
        qs.filter.return_value = qs
        qs.aggregate.return_value = {"total": 0}

        def somar(first, last, payment_method=None, excluir_metodo=None):
            if payment_method == "PRAZO":
                return 300.0
            if excluir_metodo == "PRAZO":
                return 300.0
            return 600.0

        with (
            patch("clinica_beleza.financeiro_service.somar_a_receber_periodo", side_effect=somar),
            patch("clinica_beleza.financeiro_service.somar_desconto_periodo", return_value=0),
            patch("clinica_beleza.financeiro_service.somar_contas_a_receber", return_value=0),
            patch("clinica_beleza.financeiro_service.payments_visiveis_financeiro", return_value=qs),
            patch("clinica_beleza.financeiro_service.Payment") as payment,
            patch("clinica_beleza.financeiro_service.Despesa") as despesa,
        ):
            payment.objects.filter.return_value = qs
            despesa.objects.filter.return_value = qs
            resumo = montar_resumo_financeiro(ano=2026, mes=10, today=date(2026, 10, 2))

        self.assertEqual(resumo["a_receber"], 300.0)
        self.assertEqual(resumo["a_prazo"], 300.0)
