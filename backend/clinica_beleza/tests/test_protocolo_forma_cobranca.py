from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import AgendaValidationError
from clinica_beleza.protocolo_personalizado import definir_pagamento_protocolo


class DefinirPagamentoProtocoloTest(SimpleTestCase):
    def _contrato(self, forma="POR_CONSULTA"):
        contrato = MagicMock()
        contrato.forma_cobranca = forma
        contrato.protocol_id = None
        contrato.agendamentos.values_list.return_value = [1]
        contrato.procedimentos.order_by.return_value = []
        return contrato

    def test_mesma_forma_nao_regrava(self):
        contrato = self._contrato("POR_CONSULTA")

        definir_pagamento_protocolo(contrato, "POR_CONSULTA")

        contrato.save.assert_not_called()

    @patch("clinica_beleza.models.Payment.objects")
    def test_com_recebimento_nao_troca_a_forma(self, objects):
        objects.filter.return_value.exclude.return_value.exists.return_value = True
        contrato = self._contrato("POR_CONSULTA")

        with self.assertRaisesMessage(
            AgendaValidationError,
            "Este protocolo já teve recebimento.",
        ):
            definir_pagamento_protocolo(contrato, "TOTAL", appointment_id=1)

        contrato.save.assert_not_called()

    @patch("clinica_beleza.models.Payment.objects")
    def test_sem_recebimento_aceita_trocar_a_forma(self, objects):
        objects.filter.return_value.exclude.return_value.exists.return_value = False
        contrato = self._contrato("POR_CONSULTA")

        with self.assertRaisesMessage(AgendaValidationError, "não tem procedimentos"):
            definir_pagamento_protocolo(contrato, "TOTAL", appointment_id=1)
