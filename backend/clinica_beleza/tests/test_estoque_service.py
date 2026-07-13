"""
Testes unitários para estoque_movimentacao_service.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

PATCH_ATOMIC = patch(
    'clinica_beleza.estoque_movimentacao_service.transaction.atomic',
    return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock(return_value=False)),
)


class RegistrarMovimentacaoTests(SimpleTestCase):
    """Testes para registrar_movimentacao."""

    def _produto(self, quantidade_atual=100, unidade='un'):
        p = MagicMock()
        p.quantidade_atual = Decimal(str(quantidade_atual))
        p.unidade_medida = unidade
        p.save = MagicMock()
        return p

    @PATCH_ATOMIC
    @patch('clinica_beleza.estoque_movimentacao_service.MovimentacaoEstoque')
    def test_entrada_incrementa(self, MockMov, _):
        from clinica_beleza.estoque_movimentacao_service import registrar_movimentacao
        produto = self._produto(100)
        MockMov.objects.create.return_value = MagicMock(id=1)
        registrar_movimentacao(produto, 'entrada', 10)
        self.assertEqual(produto.quantidade_atual, Decimal('110'))

    @PATCH_ATOMIC
    @patch('clinica_beleza.estoque_movimentacao_service.MovimentacaoEstoque')
    def test_saida_decrementa(self, MockMov, _):
        from clinica_beleza.estoque_movimentacao_service import registrar_movimentacao
        produto = self._produto(50)
        MockMov.objects.create.return_value = MagicMock(id=2)
        registrar_movimentacao(produto, 'saida', 20)
        self.assertEqual(produto.quantidade_atual, Decimal('30'))

    @PATCH_ATOMIC
    @patch('clinica_beleza.estoque_movimentacao_service.MovimentacaoEstoque')
    def test_ajuste_seta_valor(self, MockMov, _):
        from clinica_beleza.estoque_movimentacao_service import registrar_movimentacao
        produto = self._produto(50)
        MockMov.objects.create.return_value = MagicMock(id=3)
        registrar_movimentacao(produto, 'ajuste', 75)
        self.assertEqual(produto.quantidade_atual, Decimal('75'))

    def test_saida_estoque_insuficiente(self):
        from clinica_beleza.estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao
        produto = self._produto(5)
        with self.assertRaises(EstoqueMovimentacaoError) as ctx:
            registrar_movimentacao(produto, 'saida', 10)
        self.assertIn('insuficiente', str(ctx.exception))

    def test_tipo_invalido(self):
        from clinica_beleza.estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao
        produto = self._produto(100)
        with self.assertRaises(EstoqueMovimentacaoError) as ctx:
            registrar_movimentacao(produto, 'devolucao', 5)
        self.assertIn('Tipo deve ser', str(ctx.exception))

    def test_quantidade_zero(self):
        from clinica_beleza.estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao
        produto = self._produto(100)
        with self.assertRaises(EstoqueMovimentacaoError):
            registrar_movimentacao(produto, 'entrada', 0)

    def test_quantidade_negativa(self):
        from clinica_beleza.estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao
        produto = self._produto(100)
        with self.assertRaises(EstoqueMovimentacaoError):
            registrar_movimentacao(produto, 'entrada', -5)

    def test_quantidade_invalida_texto(self):
        from clinica_beleza.estoque_movimentacao_service import EstoqueMovimentacaoError, registrar_movimentacao
        produto = self._produto(100)
        with self.assertRaises(EstoqueMovimentacaoError):
            registrar_movimentacao(produto, 'entrada', 'abc')

    @PATCH_ATOMIC
    @patch('clinica_beleza.estoque_movimentacao_service.MovimentacaoEstoque')
    def test_movimentacao_criada_com_campos(self, MockMov, _):
        from clinica_beleza.estoque_movimentacao_service import registrar_movimentacao
        produto = self._produto(100)
        mock_mov = MagicMock(id=5)
        MockMov.objects.create.return_value = mock_mov
        result = registrar_movimentacao(
            produto, 'entrada', 10,
            motivo='Compra fornecedor',
            profissional_id=7,
            appointment_id=99,
        )
        MockMov.objects.create.assert_called_once_with(
            produto=produto,
            tipo='entrada',
            quantidade=Decimal('10'),
            motivo='Compra fornecedor',
            profissional_id=7,
            appointment_id=99,
        )
        self.assertEqual(result, mock_mov)
