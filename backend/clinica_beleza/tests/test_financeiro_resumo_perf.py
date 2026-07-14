"""Testes de agregação financeira (performance — sem N+1)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class TestSomarContasAReceber(SimpleTestCase):
    def test_usa_agregacao_sem_iterar_payments(self):
        from clinica_beleza.views_financeiro import somar_contas_a_receber

        mock_qs = MagicMock()
        chain = mock_qs.filter.return_value
        chain.annotate.return_value.annotate.return_value.annotate.return_value.aggregate.return_value = {
            "t": 150.5,
        }

        with patch("clinica_beleza.views_financeiro._payments_visiveis_financeiro", return_value=mock_qs), patch(
            "clinica_beleza.views_financeiro.PaymentParcela",
        ):
            total = somar_contas_a_receber()
        self.assertEqual(total, 150.5)
        mock_qs.filter.assert_called()
