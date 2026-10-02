"""Correção da forma de um recebimento já pago, sem mexer no valor."""
from datetime import date
from decimal import Decimal
import unittest

from clinica_beleza.forma_pagamento_correcao import plano_correcao_forma_pagamento


def _plano(**kwargs):
    base = {
        "status": "PAID",
        "payment_method": "CASH",
        "amount": Decimal("200.00"),
        "parcelas": [],
        "nova_forma": "PIX",
    }
    base.update(kwargs)
    return plano_correcao_forma_pagamento(**base)


class PlanoCorrecaoFormaTests(unittest.TestCase):
    def test_pago_sem_parcela_troca_so_a_forma(self):
        plano = _plano()
        self.assertTrue(plano["alterado"])
        self.assertEqual(plano["payment_method"], "PIX")
        self.assertEqual(plano["parcelas"], {})

    def test_pago_com_parcelas_da_mesma_forma_atualiza_todas(self):
        plano = _plano(parcelas=[
            {"id": 1, "payment_method": "CASH", "payment_date": date(2026, 10, 1), "valor": Decimal("100")},
            {"id": 2, "payment_method": "CASH", "payment_date": date(2026, 10, 1), "valor": Decimal("100")},
        ])
        self.assertEqual(plano["payment_method"], "PIX")
        self.assertEqual(plano["parcelas"], {1: "PIX", 2: "PIX"})

    def test_mesma_forma_nao_altera(self):
        plano = _plano(payment_method="PIX", nova_forma="PIX")
        self.assertFalse(plano["alterado"])

    def test_parcial_pode_corrigir_o_que_ja_entrou(self):
        plano = _plano(status="PARTIAL", amount=Decimal("100"))
        self.assertEqual(plano["payment_method"], "PIX")

    def test_pendente_recusa(self):
        with self.assertRaises(ValueError):
            _plano(status="PENDING", amount=Decimal("0"))

    def test_desconto_integral_sem_recebimento_recusa(self):
        with self.assertRaises(ValueError):
            _plano(amount=Decimal("0"))

    def test_despesa_e_prazo_nao_entram(self):
        with self.assertRaises(ValueError):
            _plano(payment_method="DESPESA")
        with self.assertRaises(ValueError):
            _plano(payment_method="PRAZO", amount=Decimal("150"))
        with self.assertRaises(ValueError):
            _plano(nova_forma="DESPESA")

    def test_formas_diferentes_exigem_o_lancamento(self):
        parcelas = [
            {"id": 1, "payment_method": "CASH", "payment_date": date(2026, 10, 1), "valor": Decimal("100")},
            {"id": 2, "payment_method": "PIX", "payment_date": date(2026, 10, 1), "valor": Decimal("100")},
        ]
        with self.assertRaises(ValueError):
            _plano(payment_method="PIX", parcelas=parcelas)
        plano = _plano(payment_method="PIX", parcelas=parcelas, nova_forma="DEBIT_CARD", parcela_id=1)
        self.assertEqual(plano["parcelas"], {1: "DEBIT_CARD"})
        self.assertEqual(plano["payment_method"], "PIX")

    def test_corrigir_a_ultima_forma_atualiza_o_cabecalho(self):
        parcelas = [
            {"id": 1, "payment_method": "CASH", "payment_date": date(2026, 10, 1), "valor": Decimal("100")},
            {"id": 2, "payment_method": "PIX", "payment_date": date(2026, 10, 2), "valor": Decimal("100")},
        ]
        plano = _plano(payment_method="PIX", parcelas=parcelas, nova_forma="CREDIT_CARD", parcela_id=2)
        self.assertEqual(plano["parcelas"], {2: "CREDIT_CARD"})
        self.assertEqual(plano["payment_method"], "CREDIT_CARD")

    def test_lancamento_inexistente(self):
        with self.assertRaises(LookupError):
            _plano(parcela_id=99)


if __name__ == "__main__":
    unittest.main()
