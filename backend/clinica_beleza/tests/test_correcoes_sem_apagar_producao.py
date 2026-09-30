"""Correções de rota, sigilo da recepção e desconto — sem apagar lançamento."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.serializers import ModelSerializer

from clinica_beleza.consulta_service.payment._common import _calcular_valor_total_com_desconto
from clinica_beleza.consulta_service.payment.receber import _ensure_payment_for_appointment
from clinica_beleza.consulta_service.lifecycle import trocar_profissional_consulta
from clinica_beleza.permissions import oculta_notas_clinicas
from clinica_beleza.serializers.consultas import ConsultaSerializer
from clinica_beleza.views_consultas.consulta_list import (
    ConsultaListView,
    ConsultaResumoFinanceiroView,
)


class RotaCriarConsultaTest(SimpleTestCase):
    def test_post_fica_na_lista_e_sai_do_resumo(self):
        self.assertTrue(callable(getattr(ConsultaListView, "post", None)))
        self.assertFalse(hasattr(ConsultaResumoFinanceiroView, "post"))


class SigiloNotasRecepcaoTest(SimpleTestCase):
    @patch("clinica_beleza.permissions._loja_and_profissional", return_value=(None, SimpleNamespace(perfil="recepcao")))
    def test_recepcao_nao_ve_nota(self, _ctx):
        self.assertTrue(oculta_notas_clinicas(MagicMock()))

    @patch("clinica_beleza.permissions._loja_and_profissional", return_value=(None, SimpleNamespace(perfil="profissional")))
    def test_profissional_ve_nota(self, _ctx):
        self.assertFalse(oculta_notas_clinicas(MagicMock()))

    @patch("clinica_beleza.permissions.oculta_notas_clinicas", return_value=True)
    @patch.object(
        ModelSerializer,
        "to_representation",
        return_value={"observacoes_gerais": "evolução", "protocolo_notas": "protocolo"},
    )
    def test_serializer_zera_notas_da_recepcao(self, _super, _oculta):
        data = ConsultaSerializer(context={"request": MagicMock()}).to_representation(MagicMock())
        self.assertEqual(data["observacoes_gerais"], "")
        self.assertEqual(data["protocolo_notas"], "")


class TrocaProfissionalAntesDeIniciarTest(SimpleTestCase):
    def test_recusa_troca_com_consulta_em_andamento(self):
        consulta = MagicMock(status="IN_PROGRESS", appointment=MagicMock(), loja_id=1)
        with self.assertRaises(ValueError):
            trocar_profissional_consulta(consulta, MagicMock(loja_id=1, is_profissional=True))
        consulta.appointment.save.assert_not_called()

    def test_grava_o_novo_profissional_sem_iniciar(self):
        consulta = MagicMock(status="SCHEDULED", loja_id=1, professional_id=4)
        professional = MagicMock(loja_id=1, is_profissional=True)
        trocar_profissional_consulta(consulta, professional)
        self.assertIs(consulta.professional, professional)
        self.assertIs(consulta.appointment.professional, professional)
        self.assertNotEqual(consulta.status, "IN_PROGRESS")


class DescontoNoTotalPendenteTest(SimpleTestCase):
    def test_omitir_desconto_mantem_o_gravado_sem_parcela(self):
        payment = SimpleNamespace(
            desconto=Decimal("200"),
            valor_total=Decimal("1500"),
            valor_pago_parcelas=Decimal(0),
        )
        self.assertEqual(
            _calcular_valor_total_com_desconto(Decimal("1500"), None, payment),
            Decimal("1300"),
        )

    def test_desconto_zero_explicito_volta_ao_bruto(self):
        payment = SimpleNamespace(
            desconto=Decimal("200"),
            valor_total=Decimal("1300"),
            valor_pago_parcelas=Decimal(0),
        )
        self.assertEqual(
            _calcular_valor_total_com_desconto(Decimal("1500"), 0, payment),
            Decimal("1500"),
        )

    @patch("clinica_beleza.consulta_service.Payment")
    @patch("clinica_beleza.consulta_service.calcular_comissao_payment_atendimento", return_value=(0, Decimal(0)))
    @patch("clinica_beleza.consulta_service._valor_pagamento_padrao", return_value=Decimal("1500"))
    @patch("clinica_beleza.consulta_service._garantir_valor_consulta_consulta")
    def test_finalizar_pendente_abate_desconto_e_mantem_o_lancamento(
        self, _garantir, _bruto, _comissao, mock_payment_model,
    ):
        payment = MagicMock(status="PENDING", desconto=Decimal("200"), valor_total=Decimal("1500"))
        mock_payment_model.objects.filter.return_value.first.return_value = payment

        atualizado = _ensure_payment_for_appointment(MagicMock(), MagicMock())

        self.assertIs(atualizado, payment)
        self.assertEqual(payment.valor_total, Decimal("1300"))
        self.assertEqual(payment.desconto, Decimal("200"))
        payment.save.assert_called_once()
        mock_payment_model.objects.filter.return_value.delete.assert_not_called()
