"""Status exibido no Financeiro quando o pagamento é parcial."""
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.models.financeiro import status_pagamento_exibido


class StatusPagamentoExibidoTest(SimpleTestCase):
    def test_pendente_sem_entrada_permanece_pendente(self):
        p = MagicMock(status="PENDING", valor_pago_parcelas=Decimal(0), saldo_devedor=Decimal("530"))
        self.assertEqual(status_pagamento_exibido(p), "PENDING")

    def test_pendente_com_entrada_vira_parcial(self):
        p = MagicMock(status="PENDING", valor_pago_parcelas=Decimal("230"), saldo_devedor=Decimal("300"))
        self.assertEqual(status_pagamento_exibido(p), "PARTIAL")

    def test_pago_e_cancelado_nao_mudam(self):
        pago = MagicMock(status="PAID", valor_pago_parcelas=Decimal("530"), saldo_devedor=Decimal(0))
        cancelado = MagicMock(status="CANCELLED", valor_pago_parcelas=Decimal(0), saldo_devedor=Decimal("530"))
        self.assertEqual(status_pagamento_exibido(pago), "PAID")
        self.assertEqual(status_pagamento_exibido(cancelado), "CANCELLED")
