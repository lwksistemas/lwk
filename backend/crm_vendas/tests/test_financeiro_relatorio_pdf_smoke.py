"""Smoke: PDF do financeiro CRM."""
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.relatorios_financeiro import _fmt_brl, _resolver_periodo, gerar_relatorio_financeiro_vendedor


class FinanceiroFmtBrlTest(SimpleTestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(_fmt_brl(1234.5), 'R$ 1.234,50')


class ResolverPeriodoFinanceiroTest(SimpleTestCase):
    def test_personalizado_iso(self):
        inicio, fim = _resolver_periodo('personalizado', '2026-06-01', '2026-06-30')
        self.assertEqual(str(inicio), '2026-06-01')
        self.assertEqual(str(fim), '2026-06-30')

    @patch('crm_vendas.services_financeiro.calcular_intervalo_vencimento', return_value=('2026-07-01', '2026-07-31'))
    def test_preset_delega_servico(self, mock_calc):
        inicio, fim = _resolver_periodo('mes_atual')
        mock_calc.assert_called_once()
        self.assertEqual(inicio, '2026-07-01')


@patch('crm_vendas.services_dashboard.calcular_intervalo_datas', return_value=('2026-06-01', '2026-06-30'))
@patch('crm_vendas.models.Oportunidade')
@patch('crm_vendas.relatorios_financeiro._obter_logo_loja', return_value=None)
@patch('crm_vendas.relatorios_financeiro.LancamentoFinanceiroCRM')
@patch('crm_vendas.relatorios_financeiro.GrupoFinanceiroCRM')
@patch('crm_vendas.relatorios_financeiro.Vendedor')
class GerarRelatorioFinanceiroPdfSmokeTest(SimpleTestCase):
    def test_gera_pdf_vazio(self, mock_vend, mock_grupo, mock_lanc, _logo, mock_opp, _periodo):
        chain = MagicMock()
        mock_lanc.objects.filter.return_value = chain
        chain.exclude.return_value = chain
        chain.filter.return_value = chain
        chain.select_related.return_value = chain
        chain.order_by.return_value = chain
        chain.aggregate.return_value = {'t': 0}
        chain.count.return_value = 0
        chain.__iter__ = lambda self: iter([])
        mock_lanc.TIPO_RECEITA = 'receita'
        mock_lanc.TIPO_DESPESA = 'despesa'
        mock_lanc.STATUS_PAGO = 'pago'
        mock_lanc.STATUS_PENDENTE = 'pendente'
        mock_lanc.STATUS_CANCELADO = 'cancelado'
        mock_opp.objects.filter.return_value.filter.return_value.aggregate.return_value = {'t': 0}

        buffer = gerar_relatorio_financeiro_vendedor(1, periodo='mes_atual')
        self.assertIsInstance(buffer, BytesIO)
        data = buffer.getvalue()
        self.assertTrue(data.startswith(b'%PDF'))
