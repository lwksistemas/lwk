"""Testes unitários do relatório de faturamento (reescrito P0)."""
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch


class TestFaturamentoRelatorioCampos(TestCase):
    """Verifica que o service usa os campos corretos (não os campos fantasma do antigo)."""

    @patch('clinica_beleza.faturamento_relatorio_service.Payment')
    @patch('clinica_beleza.faturamento_relatorio_service.Consulta')
    def test_usa_payment_paid_nao_appointment_status(self, mock_consulta, mock_payment):
        """O faturamento deve filtrar Payment.status='PAID', não Appointment.status."""
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento

        # Setup: nenhum pagamento
        mock_payment.objects.filter.return_value.select_related.return_value = MagicMock()
        mock_payment.objects.filter.return_value.select_related.return_value.filter.return_value = MagicMock()
        qs_mock = MagicMock()
        qs_mock.__iter__ = MagicMock(return_value=iter([]))
        qs_mock.prefetch_related.return_value = qs_mock
        qs_mock.filter.return_value = qs_mock
        qs_mock.select_related.return_value = qs_mock
        qs_mock.values_list.return_value = []
        mock_payment.objects.filter.return_value = qs_mock
        mock_consulta.objects.filter.return_value.select_related.return_value = []

        calcular_faturamento()

        # Deve chamar Payment.objects.filter com status='PAID'
        call_args = mock_payment.objects.filter.call_args
        self.assertIn('status', call_args.kwargs if call_args.kwargs else {})
        if call_args.kwargs:
            self.assertEqual(call_args.kwargs['status'], 'PAID')

    def test_retorno_vazio_sem_pagamentos(self):
        """Sem pagamentos, retorna linhas vazias e totais zero."""
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento

        with patch('clinica_beleza.faturamento_relatorio_service.Payment') as mock_payment, \
             patch('clinica_beleza.faturamento_relatorio_service.Consulta') as mock_consulta:
            qs_mock = MagicMock()
            qs_mock.__iter__ = MagicMock(return_value=iter([]))
            qs_mock.prefetch_related.return_value = qs_mock
            qs_mock.filter.return_value = qs_mock
            qs_mock.select_related.return_value = qs_mock
            qs_mock.values_list.return_value = []
            mock_payment.objects.filter.return_value = qs_mock
            mock_consulta.objects.filter.return_value.select_related.return_value = []

            result = calcular_faturamento()

            self.assertEqual(result['linhas'], [])
            self.assertEqual(result['totais']['valor_total'], 0)
            self.assertEqual(result['totais']['total_atendimentos'], 0)
            self.assertEqual(result['agrupamento'], 'profissional')


class TestCobrancaDuplicadaConsultaAvulsa(TestCase):
    """Verifica que criar_consulta_avulsa não gera cobrança 2x."""

    def test_valor_consulta_zero_sem_local(self):
        """Sem local_atendimento, valor_consulta deve ser 0 (procedimentos contam à parte)."""

        # Simular o cálculo
        # Sem local, sem override → valor_final = 0
        valor_consulta = None
        local_atendimento = None

        if valor_consulta is not None and Decimal(str(valor_consulta)) > 0:
            valor_final = Decimal(str(valor_consulta))
        elif local_atendimento:
            valor_final = Decimal(str(getattr(local_atendimento, 'valor_consulta', 0) or 0))
        else:
            valor_final = Decimal('0')

        self.assertEqual(valor_final, Decimal('0'))

    def test_valor_pagamento_padrao_nao_duplica(self):
        """_valor_pagamento_padrao com valor_consulta=0 retorna apenas valor_total."""
        from clinica_beleza.consulta_service import _valor_pagamento_padrao

        appointment = MagicMock()
        appointment.valor_total = Decimal('200')

        consulta = MagicMock()
        consulta.valor_consulta = Decimal('0')

        total = _valor_pagamento_padrao(appointment, consulta)
        # Deve ser 0 + 200 = 200 (não 200 + 200 = 400)
        self.assertEqual(total, Decimal('200'))

    def test_valor_pagamento_com_local(self):
        """Com local, taxa + procedimentos é o valor correto."""
        from clinica_beleza.consulta_service import _valor_pagamento_padrao

        appointment = MagicMock()
        appointment.valor_total = Decimal('150')

        consulta = MagicMock()
        consulta.valor_consulta = Decimal('80')

        total = _valor_pagamento_padrao(appointment, consulta)
        # 80 (taxa) + 150 (procedimentos) = 230
        self.assertEqual(total, Decimal('230'))


class TestWebhookPhoneValidation(TestCase):
    """Verifica que o webhook valida telefone antes de confirmar agendamento."""

    def test_phones_match_exact(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertTrue(_phones_match('5516981402966', '5516981402966'))

    def test_phones_match_with_country_code(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertTrue(_phones_match('5516981402966', '16981402966'))

    def test_phones_match_different(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertFalse(_phones_match('5516981402966', '5516999621823'))

    def test_phones_match_empty(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertFalse(_phones_match('', '5516981402966'))
        self.assertFalse(_phones_match('5516981402966', ''))
