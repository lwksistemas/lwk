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

    def test_acima_do_cadastro_rejeita(self):
        ap = MagicMock()
        ap.procedure.preco = Decimal("1200")
        appointment = _appointment_com_linhas([ap])

        with self.assertRaises(ValueError) as ctx:
            aplicar_valor_procedimentos_atendimento(appointment, "1500")
        self.assertIn("cadastrado", str(ctx.exception).lower())
        ap.save.assert_not_called()

    def test_pagamento_maior_que_o_procedimento_rejeita(self):
        from clinica_beleza.consulta_service.valores import mensagem_pagamento_acima_do_teto

        msg = mensagem_pagamento_acima_do_teto(Decimal("1200"), 0, 0, Decimal("1500"))
        self.assertIn("procedimento", msg)
        self.assertIsNone(mensagem_pagamento_acima_do_teto(Decimal("1200"), Decimal("150"), 0, Decimal("1350")))
        self.assertIn("atendimento", mensagem_pagamento_acima_do_teto(Decimal("1200"), Decimal("150"), 0, Decimal("1400")))

    def test_valor_negativo_rejeita(self):
        appointment = _appointment_com_linhas([MagicMock()])
        with self.assertRaises(ValueError):
            aplicar_valor_procedimentos_atendimento(appointment, "-10")


class GarantirTaxaComProcedimentoTests(SimpleTestCase):
    def _consulta(self, nome="BOTOX"):
        from types import SimpleNamespace

        linha = SimpleNamespace(procedure=SimpleNamespace(nome=nome), valor=Decimal("1500"))
        appointment = MagicMock()
        appointment.loja_id = 1
        appointment.protocolo_contrato_id = None
        appointment.appointment_procedures.all.return_value = [linha]
        consulta = MagicMock()
        consulta.retorno_gratuito = False
        consulta.appointment = appointment
        consulta.valor_consulta = Decimal(0)
        consulta.local_atendimento = SimpleNamespace(valor_consulta=Decimal("150"))
        return consulta

    @patch("clinica_beleza.retorno_service.cobrar_taxa_com_procedimento", return_value=False)
    def test_opcao_desligada_nao_grava_taxa_com_procedimento(self, _cobrar):
        from clinica_beleza.consulta_service.valores import _garantir_valor_consulta_consulta

        consulta = self._consulta()
        _garantir_valor_consulta_consulta(consulta)
        consulta.save.assert_not_called()

    @patch("clinica_beleza.retorno_service.cobrar_taxa_com_procedimento", return_value=False)
    def test_opcao_desligada_consulta_pura_grava_taxa(self, _cobrar):
        from clinica_beleza.consulta_service.valores import _garantir_valor_consulta_consulta

        consulta = self._consulta(nome="Consulta")
        _garantir_valor_consulta_consulta(consulta)
        self.assertEqual(consulta.valor_consulta, Decimal("150"))
        consulta.save.assert_called_once()

    @patch("clinica_beleza.retorno_service.cobrar_taxa_com_procedimento", return_value=True)
    def test_opcao_ligada_grava_taxa_com_procedimento(self, _cobrar):
        from clinica_beleza.consulta_service.valores import _garantir_valor_consulta_consulta

        consulta = self._consulta()
        _garantir_valor_consulta_consulta(consulta)
        self.assertEqual(consulta.valor_consulta, Decimal("150"))
        consulta.save.assert_called_once()
