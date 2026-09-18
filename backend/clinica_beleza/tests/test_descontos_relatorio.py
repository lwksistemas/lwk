"""Relatório de descontos concedidos."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.descontos_relatorio_service import calcular_descontos


class CalcularDescontosTest(SimpleTestCase):
    @patch("clinica_beleza.descontos_relatorio_service.payments_visiveis_financeiro")
    def test_agrupa_cliente_e_total_por_profissional(self, mock_visiveis):
        professional = MagicMock()
        professional.nome = "Marina"
        patient = MagicMock()
        patient.nome = "TAMIRES FURONI"
        convenio = MagicMock()
        convenio.nome = "Particular"
        appt = MagicMock()
        appt.professional_id = 3
        appt.professional = professional
        appt.patient_id = 1
        appt.patient = patient
        appt.convenio_id = 1
        appt.convenio = convenio
        appt.date.date.return_value.isoformat.return_value = "2026-09-18"
        appt._prefetched_objects_cache = {"appointment_procedures": []}
        appt.procedure_id = None

        payment = MagicMock()
        payment.id = 22
        payment.appointment = appt
        payment.desconto = Decimal("150.00")
        payment.notes = "Desconto: R$ 150.00"
        payment.valor_total_efetivo = Decimal("300.00")
        payment.amount = Decimal("300.00")

        qs = MagicMock()
        qs.exclude.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = qs
        qs.filter.return_value = qs
        qs.__iter__ = MagicMock(return_value=iter([payment]))
        mock_visiveis.return_value = qs

        result = calcular_descontos()

        self.assertEqual(result["totais"]["total_atendimentos"], 1)
        self.assertEqual(result["totais"]["desconto_total"], 150.0)
        self.assertEqual(result["totais"]["valor_bruto"], 450.0)
        self.assertEqual(result["totais"]["valor_liquido"], 300.0)
        prof = result["profissionais"][0]
        self.assertEqual(prof["nome"], "Marina")
        item = prof["lancamentos"][0]
        self.assertEqual(item["paciente"], "TAMIRES FURONI")
        self.assertEqual(item["desconto"], 150.0)
