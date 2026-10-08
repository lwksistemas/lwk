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
        self.assertEqual(prof["lancamentos"][0]["comissao"], 0.0)

    @patch("clinica_beleza.lancamentos_relatorio_service.comissao_do_atendimento", return_value=Decimal("48.00"))
    @patch("clinica_beleza.lancamentos_relatorio_service.payments_visiveis_financeiro")
    def test_a_prazo_usa_comissao_do_atendimento_finalizado(self, mock_visiveis, _mock_comissao):
        professional = MagicMock()
        professional.nome = "BRUNA TUCCI MARTINS"
        patient = MagicMock()
        patient.nome = "RENATA COELHO"
        appt = MagicMock()
        appt.professional_id = 2
        appt.professional = professional
        appt.patient_id = 318
        appt.patient = patient
        appt.convenio_id = None
        appt.convenio = None
        appt.date.date.return_value.isoformat.return_value = "2026-10-03"
        appt.consulta.status = "COMPLETED"

        payment = MagicMock()
        payment.id = 270
        payment.appointment = appt
        payment.payment_method = "PRAZO"
        payment.valor_total_efetivo = Decimal("120.00")
        payment.amount = Decimal("0")
        payment.comissao_valor = Decimal("0")
        payment.status = "PENDING"

        qs = MagicMock()
        qs.exclude.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = qs
        qs.filter.return_value = qs
        qs.__iter__ = MagicMock(return_value=iter([payment]))
        mock_visiveis.return_value = qs

        with patch("clinica_beleza.lancamentos_relatorio_service.status_pagamento_exibido", return_value="PENDING"):
            result = calcular_lancamentos()

        linha = result["profissionais"][0]["lancamentos"][0]
        self.assertEqual(linha["paciente"], "RENATA COELHO")
        self.assertEqual(linha["comissao"], 48.0)
        self.assertEqual(result["totais"]["comissao_total"], 48.0)
        _mock_comissao.assert_called_once()
