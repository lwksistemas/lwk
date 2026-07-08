"""Testes — POST receber consulta (total, parcial, transição de status)."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_service.payment import (
    _atualizar_status_consulta_apos_recebimento,
    registrar_recebimento_consulta,
)


class AtualizarStatusAposRecebimentoTest(SimpleTestCase):
    def test_quitou_sem_inicio_vai_para_scheduled(self):
        consulta = MagicMock(status='RECEBER', data_inicio=None)
        payment = MagicMock()
        payment.saldo_devedor = Decimal('0')

        _atualizar_status_consulta_apos_recebimento(consulta, payment)

        self.assertEqual(consulta.status, 'SCHEDULED')
        consulta.save.assert_called_once()

    def test_quitou_com_inicio_vai_para_in_progress(self):
        consulta = MagicMock(status='RECEBER', data_inicio='2026-07-08')
        payment = MagicMock()
        payment.saldo_devedor = Decimal('0')

        _atualizar_status_consulta_apos_recebimento(consulta, payment)

        self.assertEqual(consulta.status, 'IN_PROGRESS')

    def test_saldo_pendente_mantem_receber(self):
        consulta = MagicMock(status='RECEBER', data_inicio=None)
        payment = MagicMock()
        payment.saldo_devedor = Decimal('50')

        _atualizar_status_consulta_apos_recebimento(consulta, payment)

        self.assertEqual(consulta.status, 'RECEBER')


class RegistrarRecebimentoConsultaTest(SimpleTestCase):
    @patch('clinica_beleza.consulta_service.payment._atualizar_status_consulta_apos_recebimento')
    @patch('clinica_beleza.models.financeiro.PaymentParcela')
    @patch('clinica_beleza.consulta_service.Payment')
    @patch('clinica_beleza.consulta_service._garantir_valor_consulta_consulta')
    @patch('clinica_beleza.consulta_service._valor_pagamento_padrao')
    @patch('clinica_beleza.consulta_service.calcular_comissao_payment_atendimento')
    def test_recebimento_total_marca_paid(
        self,
        mock_comissao,
        mock_valor_padrao,
        _mock_garantir,
        mock_payment_model,
        _mock_parcela,
        mock_atualizar_status,
    ):
        mock_comissao.return_value = (Decimal('10'), Decimal('20'))
        mock_valor_padrao.return_value = Decimal('200')
        payment = MagicMock()
        payment.parcelas.exists.return_value = False
        payment.saldo_devedor = Decimal('200')
        mock_payment_model.objects.filter.return_value.first.return_value = None
        mock_payment_model.objects.create.return_value = payment

        consulta = MagicMock(status='RECEBER', appointment=MagicMock(loja_id=1))

        registrar_recebimento_consulta(
            consulta,
            payment_method='PIX',
            amount=Decimal('200'),
            mark_as_paid=True,
        )

        self.assertEqual(payment.status, 'PAID')
        mock_atualizar_status.assert_called_once_with(consulta, payment)

    @patch('clinica_beleza.consulta_service.payment._atualizar_status_consulta_apos_recebimento')
    @patch('clinica_beleza.models.financeiro.PaymentParcela')
    @patch('clinica_beleza.consulta_service.Payment')
    @patch('clinica_beleza.consulta_service._garantir_valor_consulta_consulta')
    @patch('clinica_beleza.consulta_service._valor_pagamento_padrao')
    @patch('clinica_beleza.consulta_service.calcular_comissao_payment_atendimento')
    def test_recebimento_parcial_cria_parcela(
        self,
        mock_comissao,
        mock_valor_padrao,
        _mock_garantir,
        mock_payment_model,
        mock_parcela_model,
        mock_atualizar_status,
    ):
        mock_comissao.return_value = (Decimal('10'), Decimal('20'))
        mock_valor_padrao.return_value = Decimal('200')
        payment = MagicMock()
        payment.loja_id = 1
        payment.parcelas.exists.return_value = False
        payment.valor_pago_parcelas = Decimal('80')
        payment.saldo_devedor = Decimal('200')
        mock_payment_model.objects.filter.return_value.first.return_value = payment

        consulta = MagicMock(status='RECEBER', appointment=MagicMock(loja_id=1))

        registrar_recebimento_consulta(
            consulta,
            payment_method='CASH',
            amount=Decimal('80'),
            mark_as_paid=False,
        )

        mock_parcela_model.objects.create.assert_called_once()
        self.assertEqual(payment.status, 'PARTIAL')
        mock_atualizar_status.assert_called_once_with(consulta, payment)

    def test_bloqueia_consulta_finalizada(self):
        consulta = MagicMock(status='COMPLETED', appointment=MagicMock())
        with self.assertRaisesMessage(ValueError, 'aberta para recebimento'):
            registrar_recebimento_consulta(consulta, amount=Decimal('50'))


class GarantirContaPendenteConsultaTest(SimpleTestCase):
    @patch('clinica_beleza.consulta_service.Payment')
    @patch('clinica_beleza.consulta_service._garantir_valor_consulta_consulta')
    @patch('clinica_beleza.consulta_service._valor_pagamento_padrao')
    @patch('clinica_beleza.consulta_service.calcular_comissao_payment_atendimento')
    def test_cria_payment_pendente_quando_receber(
        self,
        mock_comissao,
        mock_valor_padrao,
        _mock_garantir,
        mock_payment_model,
    ):
        from clinica_beleza.consulta_service.payment import garantir_conta_pendente_consulta

        mock_comissao.return_value = (Decimal('10'), Decimal('20'))
        mock_valor_padrao.return_value = Decimal('250')
        mock_payment_model.objects.filter.return_value.first.return_value = None

        consulta = MagicMock(status='RECEBER', appointment=MagicMock(loja_id=1))

        garantir_conta_pendente_consulta(consulta)

        mock_payment_model.objects.create.assert_called_once()
        kwargs = mock_payment_model.objects.create.call_args.kwargs
        self.assertEqual(kwargs['status'], 'PENDING')
        self.assertEqual(kwargs['valor_total'], Decimal('250'))
        self.assertEqual(kwargs['amount'], Decimal('0'))

    def test_ignora_quando_nao_receber(self):
        from clinica_beleza.consulta_service.payment import garantir_conta_pendente_consulta

        consulta = MagicMock(status='SCHEDULED', appointment=MagicMock())
        garantir_conta_pendente_consulta(consulta)
        consulta.appointment.assert_not_called()
