"""Testes do manager ProdutoServico (código sequencial)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.managers import ProdutoServicoManager


class ProdutoServicoCodigoManagerTests(SimpleTestCase):
    def _manager_com_ultimo(self, codigo):
        mgr = ProdutoServicoManager()
        ultimo = MagicMock()
        ultimo.codigo = codigo
        qs = MagicMock()
        qs.order_by.return_value.first.return_value = ultimo
        mgr.filter = MagicMock(return_value=qs)
        return mgr

    def test_gerar_primeiro_codigo_produto(self):
        mgr = ProdutoServicoManager()
        qs = MagicMock()
        qs.order_by.return_value.first.return_value = None
        mgr.filter = MagicMock(return_value=qs)
        self.assertEqual(mgr.gerar_proximo_codigo('produto', 1), 'P001')

    def test_gerar_primeiro_codigo_servico(self):
        mgr = ProdutoServicoManager()
        qs = MagicMock()
        qs.order_by.return_value.first.return_value = None
        mgr.filter = MagicMock(return_value=qs)
        self.assertEqual(mgr.gerar_proximo_codigo('servico', 1), 'S001')

    def test_sequencia_produto_incrementa(self):
        mgr = self._manager_com_ultimo('P003')
        self.assertEqual(mgr.gerar_proximo_codigo('produto', 1), 'P004')

    def test_codigo_invalido_reinicia_em_001(self):
        mgr = self._manager_com_ultimo('PXYZ')
        with patch('crm_vendas.managers.logger'):
            self.assertEqual(mgr.gerar_proximo_codigo('produto', 1), 'P001')

    def test_prefixo_servico_independente(self):
        mgr = self._manager_com_ultimo('S009')
        self.assertEqual(mgr.gerar_proximo_codigo('servico', 1), 'S010')
