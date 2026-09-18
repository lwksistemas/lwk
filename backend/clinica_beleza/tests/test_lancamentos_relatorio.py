"""Relatório de lançamentos por profissional."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.lancamentos_relatorio_service import calcular_lancamentos


class CalcularLancamentosTest(SimpleTestCase):
    @patch("clinica_beleza.lancamentos_relatorio_service.payments_visiveis_financeiro")
    def test_agrupa_paciente_por_profissional(self, mock_visiveis):
        professional = MagicMock()
        professional.nome = "Nayara"
        patient = MagicMock()
        patient.nome = "LUIZ HENRIQUE FELIX"
        convenio = MagicMock()
        convenio.nome = "Família/Funcionário"
        appt = MagicMock()
        appt.professional_id = 9
        appt.professional = professional
        appt.patient_id = 1
        appt.patient = patient
        appt.convenio_id = 2
        appt.convenio = convenio
        appt.date.date.return_value.isoformat.return_value = "2026-09-18"
        appt._prefetched_objects_cache = {"appointment_procedures": []}
        appt.procedure_id = None

        payment = MagicMock()
        payment.id = 10
        payment.appointment = appt
        payment.payment_method = "DESPESA"
        payment.valor_total_efetivo = Decimal("280.00")
        payment.amount = Decimal("280.00")
        payment.comissao_valor = Decimal("0")
        payment.status = "PAID"

        qs = MagicMock()
        qs.exclude.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = qs
        qs.filter.return_value = qs
        qs.__iter__ = MagicMock(return_value=iter([payment]))
        mock_visiveis.return_value = qs

        with patch("clinica_beleza.lancamentos_relatorio_service.status_pagamento_exibido", return_value="PAID"):
            result = calcular_lancamentos()

        self.assertEqual(result["totais"]["total_atendimentos"], 1)
        self.assertEqual(result["totais"]["valor_total"], 280.0)
        prof = result["profissionais"][0]
        self.assertEqual(prof["nome"], "Nayara")
        self.assertEqual(prof["lancamentos"][0]["paciente"], "LUIZ HENRIQUE FELIX")
        self.assertEqual(prof["lancamentos"][0]["forma_pagamento"], "DESPESA")
