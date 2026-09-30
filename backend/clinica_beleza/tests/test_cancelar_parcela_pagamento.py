"""Correção do histórico: remover um lançamento sem apagar a linha."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.financeiro_service import cancelar_parcela_pagamento


@contextmanager
def _atomic():
    yield


class CancelarParcelaHistoricoTest(SimpleTestCase):
    def _payment(self, pagas):
        payment = MagicMock()
        payment.pk = 237
        payment.valor_total_efetivo = Decimal("6000")
        payment.data_vencimento = date(2026, 10, 12)
        payment.payment_method = "CASH"
        payment.parcelas.filter.return_value.order_by.return_value = pagas
        payment._prefetched_objects_cache = {"parcelas": [MagicMock(status="CANCELLED")]}
        return payment

    @patch("clinica_beleza.estoque_service.tenant_atomic", _atomic)
    @patch("clinica_beleza.financeiro_service.PaymentParcela.objects")
    def test_remover_um_de_dois_mantem_o_outro_como_parcial(self, objects):
        parcela = MagicMock(status="PAID", valor=Decimal("650"))
        objects.select_for_update.return_value.filter.return_value.first.return_value = parcela
        restante = SimpleNamespace(
            valor=Decimal("650"),
            payment_method="CASH",
            payment_date=date(2026, 9, 30),
        )
        payment = self._payment([restante])

        cancelar_parcela_pagamento(payment, 229)

        self.assertEqual(parcela.status, "CANCELLED")
        parcela.save.assert_called_once_with(update_fields=["status"])
        self.assertEqual(payment.status, "PARTIAL")
        self.assertEqual(payment.amount, Decimal("650"))
        self.assertEqual(payment.payment_method, "CASH")
        self.assertNotIn("parcelas", payment._prefetched_objects_cache)

    @patch("clinica_beleza.estoque_service.tenant_atomic", _atomic)
    @patch("clinica_beleza.financeiro_service.PaymentParcela.objects")
    def test_remover_o_unico_recebido_volta_para_a_prazo(self, objects):
        parcela = MagicMock(status="PAID")
        objects.select_for_update.return_value.filter.return_value.first.return_value = parcela
        payment = self._payment([])

        cancelar_parcela_pagamento(payment, 230)

        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(payment.amount, Decimal(0))
        self.assertIsNone(payment.payment_date)
        self.assertEqual(payment.payment_method, "PRAZO")

    @patch("clinica_beleza.estoque_service.tenant_atomic", _atomic)
    @patch("clinica_beleza.financeiro_service.PaymentParcela.objects")
    def test_lancamento_ja_removido_nao_recalcula(self, objects):
        parcela = MagicMock(status="CANCELLED")
        objects.select_for_update.return_value.filter.return_value.first.return_value = parcela
        payment = self._payment([])

        with self.assertRaises(ValueError):
            cancelar_parcela_pagamento(payment, 229)

        payment.save.assert_not_called()

    @patch("clinica_beleza.estoque_service.tenant_atomic", _atomic)
    @patch("clinica_beleza.financeiro_service.PaymentParcela.objects")
    def test_lancamento_de_outro_pagamento_nao_existe(self, objects):
        objects.select_for_update.return_value.filter.return_value.first.return_value = None
        payment = self._payment([])

        with self.assertRaises(LookupError):
            cancelar_parcela_pagamento(payment, 999)
