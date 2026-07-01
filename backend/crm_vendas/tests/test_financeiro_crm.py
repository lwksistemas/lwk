"""Testes do financeiro CRM."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.response import Response

from crm_vendas.mixins import CRMSchemaRecoveryMixin
from crm_vendas.services_financeiro import sincronizar_receita_comissao_oportunidade


class TestCRMSchemaRecoveryMixinSuper(TestCase):
    """Regressão: super() dentro de lambda quebrava list/create no Python 3.12."""

    def test_list_chama_super_sem_runtime_error(self):
        class Parent:
            def list(self, request, *args, **kwargs):
                return Response({'ok': True})

        class Child(CRMSchemaRecoveryMixin, Parent):
            pass

        resp = Child().list(MagicMock())
        self.assertEqual(resp.data, {'ok': True})


class TestCalcularIntervaloVencimento(TestCase):
    def test_mes_atual_inclui_vencimentos_futuros_no_mes(self):
        from crm_vendas.services_financeiro import calcular_intervalo_vencimento

        with patch('crm_vendas.services_financeiro.timezone') as mock_tz:
            mock_tz.now.return_value.date.return_value = date(2026, 7, 1)
            inicio, fim = calcular_intervalo_vencimento('mes_atual')
        self.assertEqual(inicio, date(2026, 7, 1))
        self.assertEqual(fim, date(2026, 7, 31))


class TestSincronizarReceitaComissao(TestCase):
    def test_cria_receita_quando_ganha_com_comissao(self):
        oportunidade = MagicMock()
        oportunidade.id = 10
        oportunidade.loja_id = 1
        oportunidade.vendedor_id = 5
        oportunidade.etapa = 'closed_won'
        oportunidade.valor_comissao = Decimal('150.00')
        oportunidade.titulo = 'Venda ABC'
        oportunidade.data_fechamento_ganho = date(2026, 6, 15)
        oportunidade.data_fechamento = None

        with patch('crm_vendas.models.financeiro.LancamentoFinanceiroCRM') as mock_lanc, patch(
            'crm_vendas.services_financeiro._grupo_comissao',
            return_value=MagicMock(id=1),
        ), patch('crm_vendas.services_financeiro.garantir_grupos_padrao'):
            mock_lanc.objects.filter.return_value.first.return_value = None
            mock_lanc.ORIGEM_COMISSAO = 'comissao_venda'
            mock_lanc.TIPO_RECEITA = 'receita'
            mock_lanc.STATUS_PENDENTE = 'pendente'
            mock_lanc.STATUS_CANCELADO = 'cancelado'
            sincronizar_receita_comissao_oportunidade(oportunidade)
            mock_lanc.objects.create.assert_called_once()
            kwargs = mock_lanc.objects.create.call_args.kwargs
            self.assertEqual(kwargs['valor'], Decimal('150.00'))
            self.assertEqual(kwargs['vendedor_id'], 5)

    def test_cancela_quando_perde(self):
        oportunidade = MagicMock()
        oportunidade.id = 10
        oportunidade.loja_id = 1
        oportunidade.vendedor_id = 5
        oportunidade.etapa = 'closed_lost'

        existente = MagicMock()
        existente.status = 'pendente'

        with patch('crm_vendas.models.financeiro.LancamentoFinanceiroCRM') as mock_lanc:
            mock_lanc.objects.filter.return_value.first.return_value = existente
            mock_lanc.ORIGEM_COMISSAO = 'comissao_venda'
            mock_lanc.STATUS_CANCELADO = 'cancelado'
            sincronizar_receita_comissao_oportunidade(oportunidade)
            self.assertEqual(existente.status, 'cancelado')
            existente.save.assert_called_once()


class TestResumoFinanceiroComissao(TestCase):
    def test_comissao_usa_soma_valor_comissao_oportunidades(self):
        from unittest.mock import MagicMock, patch

        from crm_vendas.services_financeiro import resumo_financeiro_crm

        mock_lanc = MagicMock()
        mock_lanc.objects.filter.return_value.exclude.return_value.filter.return_value = mock_lanc
        mock_lanc.objects.filter.return_value.exclude.return_value.filter.return_value.filter.return_value = mock_lanc
        mock_lanc.TIPO_RECEITA = 'receita'
        mock_lanc.TIPO_DESPESA = 'despesa'
        mock_lanc.STATUS_PAGO = 'pago'
        mock_lanc.STATUS_PENDENTE = 'pendente'
        mock_lanc.STATUS_CANCELADO = 'cancelado'
        mock_lanc.objects.filter.return_value.exclude.return_value.filter.return_value.aggregate.return_value = {
            't': 33375.0,
        }

        mock_opp = MagicMock()
        mock_opp.objects.filter.return_value.filter.return_value.aggregate.return_value = {'t': 4875.0}

        with patch('crm_vendas.models.financeiro.LancamentoFinanceiroCRM', mock_lanc), patch(
            'crm_vendas.models.Oportunidade', mock_opp
        ), patch(
            'crm_vendas.services_dashboard.calcular_intervalo_datas',
            return_value=(date(2026, 5, 1), date(2026, 5, 31)),
        ), patch(
            'crm_vendas.services_dashboard._filtro_fechamento_no_periodo',
            return_value=MagicMock(),
        ):
            out = resumo_financeiro_crm(1, None, periodo='mes_passado')
            self.assertEqual(out['comissao_vendas_total'], 4875.0)


class TestSincronizarComissoesRetroativas(TestCase):
    def test_dry_run_conta_oportunidades(self):
        with patch('crm_vendas.models.Oportunidade') as mock_opp, patch(
            'crm_vendas.services_financeiro.garantir_grupos_padrao',
        ), patch('crm_vendas.models.financeiro.LancamentoFinanceiroCRM') as mock_lanc:
            chain = mock_opp.objects.filter.return_value
            chain.exclude.return_value.exclude.return_value.exclude.return_value.select_related.return_value.order_by.return_value.count.return_value = 2
            chain.exclude.return_value.exclude.return_value.exclude.return_value.select_related.return_value.order_by.return_value.iterator.return_value = iter([])
            mock_lanc.objects.filter.return_value.first.return_value = None
            mock_lanc.ORIGEM_COMISSAO = 'comissao_venda'
            from crm_vendas.services_financeiro import sincronizar_comissoes_retroativas
            out = sincronizar_comissoes_retroativas(1, dry_run=True)
            self.assertEqual(out['oportunidades_analisadas'], 2)


class TestRecorrenciaFinanceiro(TestCase):
    def test_adicionar_periodo_mensal(self):
        from crm_vendas.services_recorrencia_financeiro import _adicionar_periodo

        self.assertEqual(_adicionar_periodo(date(2026, 1, 31), 'mensal'), date(2026, 2, 28))
        self.assertEqual(_adicionar_periodo(date(2026, 6, 15), 'mensal'), date(2026, 7, 15))

    def test_adicionar_periodo_trimestral(self):
        from crm_vendas.services_recorrencia_financeiro import _adicionar_periodo

        self.assertEqual(_adicionar_periodo(date(2026, 3, 10), 'trimestral'), date(2026, 6, 10))

    def test_criar_recorrencia_vincula_primeiro_lancamento(self):
        from crm_vendas.services_recorrencia_financeiro import criar_recorrencia_com_primeiro_lancamento

        grupo = MagicMock(id=3)
        with patch('crm_vendas.models.financeiro.RecorrenciaFinanceiroCRM') as mock_rec, patch(
            'crm_vendas.models.financeiro.LancamentoFinanceiroCRM'
        ) as mock_lanc:
            mock_rec.objects.create.return_value = MagicMock(id=99)
            mock_lanc.ORIGEM_MANUAL = 'manual'
            mock_lanc.objects.create.return_value = MagicMock(id=100)
            rec, lanc = criar_recorrencia_com_primeiro_lancamento(
                1,
                vendedor_id=5,
                tipo='despesa',
                descricao='Aluguel',
                valor=Decimal('1200.00'),
                data_vencimento=date(2026, 7, 5),
                frequencia='mensal',
                grupo=grupo,
            )
            self.assertEqual(rec.id, 99)
            self.assertEqual(lanc.id, 100)
            mock_lanc.objects.create.assert_called_once()
            kwargs = mock_lanc.objects.create.call_args.kwargs
            self.assertEqual(kwargs['recorrencia'].id, 99)
            self.assertEqual(kwargs['grupo'], grupo)
