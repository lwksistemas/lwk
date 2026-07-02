"""Testes de snapshot e agregação do relatório de comissão."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.relatorio_comissao_data import (
    agregar_totais_oportunidades,
    montar_dados_oportunidades_snapshot,
    resumo_relatorio_comissao,
)


class AgregarTotaisOportunidadesTest(SimpleTestCase):
    def test_delega_aggregate(self):
        qs = MagicMock()
        qs.aggregate.return_value = {
            'total_vendas': Decimal('5000'),
            'total_comissao': Decimal('500'),
            'qtd': 3,
        }
        out = agregar_totais_oportunidades(qs)
        self.assertEqual(out['qtd'], 3)
        qs.aggregate.assert_called_once()


class MontarDadosOportunidadesSnapshotTest(SimpleTestCase):
    def _opp(self, *, com_conta=False):
        op = MagicMock()
        op.titulo = 'Venda A'
        op.valor = Decimal('2000')
        op.valor_comissao = Decimal('200')
        op.data_fechamento_ganho = date(2026, 6, 10)
        op.data_fechamento = None
        op.lead = MagicMock()
        if com_conta:
            op.lead.conta_id = 5
            op.lead.conta.nome = 'Conta Cliente'
            op.lead.conta.cnpj = '12345678000190'
            op.lead.nome = 'Lead'
            op.lead.cpf_cnpj = ''
        else:
            op.lead.conta_id = None
            op.lead.nome = 'Lead Direto'
            op.lead.cpf_cnpj = '12345678901'
        return op

    def test_monta_linha_com_lead(self):
        qs = MagicMock()
        qs.order_by.return_value = [self._opp()]
        dados = montar_dados_oportunidades_snapshot(qs)
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['valor'], 2000.0)
        self.assertIn('Lead Direto', dados[0]['cliente'])

    def test_monta_linha_com_conta(self):
        qs = MagicMock()
        qs.order_by.return_value = [self._opp(com_conta=True)]
        dados = montar_dados_oportunidades_snapshot(qs)
        self.assertIn('Conta Cliente', dados[0]['cliente'])


class ResumoRelatorioComissaoTest(SimpleTestCase):
    @patch('crm_vendas.relatorio_comissao_data.queryset_oportunidades_comissao')
    @patch('crm_vendas.relatorio_comissao_data.resolver_periodo_relatorio')
    @patch('crm_vendas.models.Conta')
    def test_resumo_com_vendas(self, mock_conta, mock_periodo, mock_qs_fn):
        ep = MagicMock(id=10, nome='EP Teste')
        mock_conta.objects.filter.return_value.first.return_value = ep
        mock_periodo.return_value = (date(2026, 6, 1), date(2026, 6, 30), 'Junho 2026', None)

        chain = MagicMock()
        mock_qs_fn.return_value = chain
        chain.aggregate.return_value = {'total_vendas': 8000, 'total_comissao': 800, 'qtd': 2}
        chain.order_by.return_value.__getitem__.return_value = []

        resumo, err = resumo_relatorio_comissao(1, 10, vendedor_id=None)
        self.assertIsNone(err)
        self.assertEqual(resumo['quantidade_vendas'], 2)
        self.assertEqual(resumo['valor_total_comissao'], 800.0)

    @patch('crm_vendas.models.Conta')
    def test_empresa_inexistente(self, mock_conta):
        mock_conta.objects.filter.return_value.first.return_value = None
        resumo, err = resumo_relatorio_comissao(1, 999, None)
        self.assertIsNone(resumo)
        self.assertIn('prestadora', (err or '').lower())
