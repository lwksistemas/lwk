"""Override do valor dos procedimentos no recebimento."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_service.valores import aplicar_valor_procedimentos_atendimento


def _appointment_com_linhas(linhas):
    qs = MagicMock()
    qs.select_related.return_value.order_by.return_value = linhas
    appointment = MagicMock(procedure_id=1, loja_id=9)
    appointment.appointment_procedures = qs
    return appointment


class AplicarValorProcedimentosTests(SimpleTestCase):
    def test_uma_linha_grava_override(self):
        ap = MagicMock()
        appointment = _appointment_com_linhas([ap])

        result = aplicar_valor_procedimentos_atendimento(appointment, "80")

        self.assertEqual(result, Decimal("80"))
        self.assertEqual(ap.valor, Decimal("80"))
        ap.save.assert_called_once_with(update_fields=["valor"])
        self.assertIsNone(appointment._valor_total_cache)

    def test_varias_linhas_rateia_proporcionalmente(self):
        ap1 = MagicMock()
        ap1.get_valor.return_value = Decimal("100")
        ap2 = MagicMock()
        ap2.get_valor.return_value = Decimal("50")
        appointment = _appointment_com_linhas([ap1, ap2])

        aplicar_valor_procedimentos_atendimento(appointment, "300")

        self.assertEqual(ap1.valor, Decimal("200.00"))
        self.assertEqual(ap2.valor, Decimal("100.00"))

    def test_sem_procedimento_rejeita(self):
        appointment = _appointment_com_linhas([])
        appointment.procedure_id = None

        with self.assertRaises(ValueError) as ctx:
            aplicar_valor_procedimentos_atendimento(appointment, "80")
        self.assertIn("procedimento", str(ctx.exception).lower())

    def test_sem_linhas_cria_appointment_procedure(self):
        appointment = _appointment_com_linhas([])
        appointment.procedure_id = 4
        appointment.loja_id = 9

        with patch("clinica_beleza.models.AppointmentProcedure") as mock_ap:
            aplicar_valor_procedimentos_atendimento(appointment, "120")
        mock_ap.objects.create.assert_called_once()
        kwargs = mock_ap.objects.create.call_args.kwargs
        self.assertEqual(kwargs["procedure_id"], 4)
        self.assertEqual(kwargs["valor"], Decimal("120"))

    def test_valor_negativo_rejeita(self):
        appointment = _appointment_com_linhas([MagicMock()])
        with self.assertRaises(ValueError):
            aplicar_valor_procedimentos_atendimento(appointment, "-10")
