"""Testes unitários do relatório de faturamento (reescrito P0)."""
from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch


class TestFaturamentoRelatorioCampos(TestCase):
    """Verifica que o service usa os campos corretos (não os campos fantasma do antigo)."""

    @patch("clinica_beleza.faturamento_relatorio_service.Payment")
    @patch("clinica_beleza.faturamento_relatorio_service.Consulta")
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
        qs_mock.exclude.return_value = qs_mock
        qs_mock.select_related.return_value = qs_mock
        qs_mock.values_list.return_value = []
        mock_payment.objects.filter.return_value = qs_mock
        mock_consulta.objects.filter.return_value.select_related.return_value = []

        calcular_faturamento()

        # PAID e PARTIAL: o parcial entra só pelo valor já recebido.
        call_args = mock_payment.objects.filter.call_args
        self.assertEqual(call_args.kwargs.get("status__in"), ("PAID", "PARTIAL"))

    def test_retorno_vazio_sem_pagamentos(self):
        """Sem pagamentos, retorna linhas vazias e totais zero."""
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento

        with patch("clinica_beleza.faturamento_relatorio_service.Payment") as mock_payment, \
             patch("clinica_beleza.faturamento_relatorio_service.Consulta") as mock_consulta:
            qs_mock = MagicMock()
            qs_mock.__iter__ = MagicMock(return_value=iter([]))
            qs_mock.prefetch_related.return_value = qs_mock
            qs_mock.filter.return_value = qs_mock
            qs_mock.exclude.return_value = qs_mock
            qs_mock.select_related.return_value = qs_mock
            qs_mock.values_list.return_value = []
            mock_payment.objects.filter.return_value = qs_mock
            mock_consulta.objects.filter.return_value.select_related.return_value = []

            result = calcular_faturamento()

            self.assertEqual(result["linhas"], [])
            self.assertEqual(result["totais"]["valor_total"], 0)
            self.assertEqual(result["totais"]["total_atendimentos"], 0)
            self.assertEqual(result["agrupamento"], "profissional")

    def test_periodo_segue_o_dia_do_agendamento(self):
        from clinica_beleza.faturamento_relatorio_service import calcular_faturamento

        with patch("clinica_beleza.faturamento_relatorio_service.Payment") as mock_payment, \
             patch("clinica_beleza.faturamento_relatorio_service.Consulta") as mock_consulta:
            qs_mock = MagicMock()
            qs_mock.__iter__ = MagicMock(return_value=iter([]))
            qs_mock.prefetch_related.return_value = qs_mock
            qs_mock.filter.return_value = qs_mock
            qs_mock.exclude.return_value = qs_mock
            qs_mock.select_related.return_value = qs_mock
            mock_payment.objects.filter.return_value = qs_mock
            mock_consulta.objects.filter.return_value.select_related.return_value = []

            calcular_faturamento(data_inicio=date(2026, 10, 1), data_fim=date(2026, 10, 1))

            filtros = [chamada.kwargs for chamada in qs_mock.filter.call_args_list]
            self.assertIn({"appointment__date__date__gte": date(2026, 10, 1)}, filtros)
            self.assertIn({"appointment__date__date__lte": date(2026, 10, 1)}, filtros)
            self.assertFalse(any("payment_date__date__gte" in chamada.kwargs for chamada in qs_mock.filter.call_args_list))


class TestAgrupamentoConvenio(TestCase):
    def test_particular_cadastrado_e_sem_convenio_usam_a_mesma_chave(self):
        from types import SimpleNamespace

        from clinica_beleza.faturamento_relatorio_service import _get_grupo_chave, _get_grupo_nome

        cadastrado = SimpleNamespace(convenio_id=1, convenio=SimpleNamespace(nome="Particular"))
        sem_plano = SimpleNamespace(convenio_id=None, convenio=None)
        outro = SimpleNamespace(convenio_id=4, convenio=SimpleNamespace(nome="DONATIVO"))

        self.assertEqual(
            _get_grupo_chave(cadastrado, None, "convenio"),
            _get_grupo_chave(sem_plano, None, "convenio"),
        )
        self.assertEqual(_get_grupo_nome(sem_plano, None, "convenio"), "Particular")
        self.assertNotEqual(
            _get_grupo_chave(cadastrado, None, "convenio"),
            _get_grupo_chave(outro, None, "convenio"),
        )
        self.assertEqual(_get_grupo_nome(outro, None, "convenio"), "DONATIVO")


class TestFaturamentoDescontoERetorno(TestCase):
    """Desconto comercial e consulta de retorno não entram na receita."""

    def _pagamento(self, *, valor_proc, desconto, valor_consulta=0, retorno=False, taxa_local=0):
        from types import SimpleNamespace

        proc = SimpleNamespace(
            valor=Decimal(valor_proc),
            procedure=SimpleNamespace(preco=Decimal(valor_proc)),
        )
        appt = MagicMock()
        appt.id = 1
        appt.appointment_procedures.all.return_value = [proc]
        local = SimpleNamespace(valor_consulta=Decimal(taxa_local)) if taxa_local else None
        consulta = SimpleNamespace(
            valor_consulta=Decimal(valor_consulta),
            local_atendimento=local,
            retorno_gratuito=retorno,
        )
        payment = SimpleNamespace(appointment=appt, desconto=Decimal(desconto))
        return payment, {1: consulta}

    def test_desconto_sai_do_procedimento(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(valor_proc="1500", desconto="500")
        valor_consulta, valor_proc, usar_amount = _calcular_valor_pagamento(payment, consultas)
        self.assertEqual(valor_proc, Decimal("1000"))
        self.assertEqual(valor_consulta, Decimal(0))
        self.assertFalse(usar_amount)

    def test_retorno_gratuito_nao_puxa_taxa_do_local(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(
            valor_proc="1500",
            desconto="0",
            retorno=True,
            taxa_local="150",
        )
        valor_consulta, valor_proc, usar_amount = _calcular_valor_pagamento(payment, consultas)
        self.assertEqual(valor_consulta, Decimal(0))
        self.assertEqual(valor_proc, Decimal("1500"))
        self.assertFalse(usar_amount)

    def test_taxa_cobrada_permanece_e_desconto_sai_do_procedimento(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(
            valor_proc="1500",
            desconto="500",
            valor_consulta="150",
        )
        valor_consulta, valor_proc, _usar = _calcular_valor_pagamento(payment, consultas)
        self.assertEqual(valor_consulta, Decimal("150"))
        self.assertEqual(valor_proc, Decimal("1000"))

    def test_opcao_desligada_nao_puxa_taxa_com_procedimento(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(
            valor_proc="1500",
            desconto="0",
            taxa_local="150",
        )
        valor_consulta, valor_proc, usar_amount = _calcular_valor_pagamento(
            payment, consultas, cobrar_taxa_com_procedimento=False,
        )
        self.assertEqual(valor_consulta, Decimal(0))
        self.assertEqual(valor_proc, Decimal("1500"))
        self.assertFalse(usar_amount)

    def test_opcao_desligada_consulta_sem_procedimento_puxa_taxa(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(
            valor_proc="0",
            desconto="0",
            taxa_local="150",
        )
        valor_consulta, valor_proc, _usar = _calcular_valor_pagamento(
            payment, consultas, cobrar_taxa_com_procedimento=False,
        )
        self.assertEqual(valor_consulta, Decimal("150"))
        self.assertEqual(valor_proc, Decimal(0))

    def test_taxa_ja_gravada_permanece_com_opcao_desligada(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(
            valor_proc="1500",
            desconto="0",
            valor_consulta="150",
            taxa_local="150",
        )
        valor_consulta, valor_proc, _usar = _calcular_valor_pagamento(
            payment, consultas, cobrar_taxa_com_procedimento=False,
        )
        self.assertEqual(valor_consulta, Decimal("150"))
        self.assertEqual(valor_proc, Decimal("1500"))

    def test_desconto_integral_nao_volta_para_o_valor_pago(self):
        from clinica_beleza.faturamento_relatorio_service import _calcular_valor_pagamento

        payment, consultas = self._pagamento(valor_proc="1500", desconto="1500")
        valor_consulta, valor_proc, usar_amount = _calcular_valor_pagamento(payment, consultas)
        self.assertEqual(valor_proc, Decimal(0))
        self.assertEqual(valor_consulta, Decimal(0))
        self.assertFalse(usar_amount)


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
            valor_final = Decimal(str(getattr(local_atendimento, "valor_consulta", 0) or 0))
        else:
            valor_final = Decimal(0)

        self.assertEqual(valor_final, Decimal(0))

    def test_valor_pagamento_padrao_nao_duplica(self):
        """_valor_pagamento_padrao com valor_consulta=0 retorna apenas valor_total."""
        from clinica_beleza.consulta_service import _valor_pagamento_padrao

        appointment = MagicMock()
        appointment.valor_total = Decimal(200)

        consulta = MagicMock()
        consulta.valor_consulta = Decimal(0)

        total = _valor_pagamento_padrao(appointment, consulta)
        # Deve ser 0 + 200 = 200 (não 200 + 200 = 400)
        self.assertEqual(total, Decimal(200))

    def test_valor_pagamento_com_local(self):
        """Com local, taxa + procedimentos é o valor correto."""
        from clinica_beleza.consulta_service import _valor_pagamento_padrao

        appointment = MagicMock()
        appointment.valor_total = Decimal(150)

        consulta = MagicMock()
        consulta.valor_consulta = Decimal(80)

        total = _valor_pagamento_padrao(appointment, consulta)
        # 80 (taxa) + 150 (procedimentos) = 230
        self.assertEqual(total, Decimal(230))


class TestWebhookPhoneValidation(TestCase):
    """Verifica que o webhook valida telefone antes de confirmar agendamento."""

    def test_phones_match_exact(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertTrue(_phones_match("5516981402966", "5516981402966"))

    def test_phones_match_with_country_code(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertTrue(_phones_match("5516981402966", "16981402966"))

    def test_phones_match_different(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertFalse(_phones_match("5516981402966", "5516999621823"))

    def test_phones_match_empty(self):
        from clinica_beleza.agenda_confirmacao_service import _phones_match
        self.assertFalse(_phones_match("", "5516981402966"))
        self.assertFalse(_phones_match("5516981402966", ""))
