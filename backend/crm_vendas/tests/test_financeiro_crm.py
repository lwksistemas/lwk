"""Testes do financeiro CRM."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from crm_vendas.services_financeiro import sincronizar_receita_comissao_oportunidade


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
