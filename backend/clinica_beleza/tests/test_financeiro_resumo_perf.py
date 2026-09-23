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
