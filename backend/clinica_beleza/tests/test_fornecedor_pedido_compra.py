"""Testes de fornecedor, catálogo e pedido de compra (sem entrada de estoque)."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.fornecedor_service import (
    FornecedorError,
    importar_catalogo,
    preview_catalogo_arquivo,
    salvar_fornecedor,
)
from clinica_beleza.pedido_compra_service import (
    PedidoCompra,
    PedidoCompraError,
    assinar_clinica,
    criar_pedido,
    enviar_pedido_assinado,
)


class PreviewCatalogoTests(SimpleTestCase):
    def test_csv_com_cabecalho(self):
        texto = "codigo;nome;unidade;preco\nBOTX01;Botox 100u;un;850,00\n"
        itens = preview_catalogo_arquivo(texto)
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["codigo"], "BOTX01")
        self.assertEqual(itens[0]["nome"], "Botox 100u")
        self.assertEqual(itens[0]["preco_ref"], "850.00")

    def test_sem_codigo_e_nome_falha(self):
        with self.assertRaises(FornecedorError):
            preview_catalogo_arquivo("codigo;nome\n;\n;;\n")

    def test_vazio_falha(self):
        with self.assertRaises(FornecedorError):
            preview_catalogo_arquivo("")


class SalvarFornecedorTests(SimpleTestCase):
    @patch("clinica_beleza.fornecedor_service.existe_documento_duplicado", return_value=True)
    def test_cnpj_duplicado(self, _dup):
        with self.assertRaises(FornecedorError) as ctx:
            salvar_fornecedor(1, {"cnpj": "11.222.333/0001-81", "razao_social": "ACME"})
        self.assertIn("fornecedor", str(ctx.exception).lower())

    def test_cnpj_invalido(self):
        with self.assertRaises(FornecedorError):
            salvar_fornecedor(1, {"cnpj": "123", "razao_social": "ACME"})


class ImportarCatalogoTests(SimpleTestCase):
    @patch("clinica_beleza.fornecedor_service.FornecedorProduto")
    def test_upsert_por_codigo(self, MockProd):
        MockProd.objects.update_or_create.side_effect = [
            (MagicMock(), True),
            (MagicMock(), False),
        ]
        forn = MagicMock(loja_id=1)
        res = importar_catalogo(forn, [
            {"codigo": "A", "nome": "Um", "unidade": "un", "preco_ref": "10"},
            {"codigo": "A", "nome": "Um atualizado", "unidade": "un", "preco_ref": "12"},
        ])
        self.assertEqual(res["criados"], 1)
        self.assertEqual(res["atualizados"], 1)
        self.assertEqual(MockProd.objects.update_or_create.call_count, 2)


class PedidoCompraServiceTests(SimpleTestCase):
    @patch("clinica_beleza.pedido_compra_service.Fornecedor")
    def test_pedido_sem_item(self, MockForn):
        MockForn.objects.filter.return_value.first.return_value = MagicMock(id=1)
        with self.assertRaises(PedidoCompraError) as ctx:
            criar_pedido(1, {"fornecedor_id": 1, "itens": []})
        self.assertIn("item", str(ctx.exception).lower())

    def test_assinatura_incompleta_bloqueia_envio(self):
        pedido = MagicMock()
        pedido.status = PedidoCompra.STATUS_AGUARDANDO_FORNECEDOR
        with self.assertRaises(PedidoCompraError) as ctx:
            enviar_pedido_assinado(pedido, ["email"])
        self.assertIn("assinado", str(ctx.exception).lower())

    @patch("clinica_beleza.estoque_movimentacao_service.registrar_movimentacao")
    @patch("clinica_beleza.pedido_compra_service.PedidoCompraItem")
    @patch("clinica_beleza.pedido_compra_service.PedidoCompra.objects")
    @patch("clinica_beleza.pedido_compra_service.Fornecedor")
    @patch("clinica_beleza.pedido_compra_service.transaction.atomic")
    def test_criar_pedido_nao_altera_estoque(self, mock_atomic, MockForn, mock_ped_objs, _Item, mock_mov):
        mock_atomic.return_value = MagicMock(
            __enter__=MagicMock(), __exit__=MagicMock(return_value=False),
        )
        MockForn.objects.filter.return_value.first.return_value = MagicMock(id=1)
        pedido = MagicMock(id=9, numero=1)
        qs = MagicMock()
        qs.delete.return_value = None
        qs.__iter__.return_value = iter([])
        pedido.itens.all.return_value = qs
        mock_ped_objs.create.return_value = pedido
        mock_ped_objs.filter.return_value.aggregate.return_value = {"m": 0}
        criar_pedido(1, {
            "fornecedor_id": 1,
            "itens": [{"codigo": "X", "nome": "Produto", "quantidade": 2, "preco": "10"}],
        })
        mock_mov.assert_not_called()

    def test_assinar_clinica_exige_nome(self):
        pedido = MagicMock()
        pedido.status = PedidoCompra.STATUS_RASCUNHO
        pedido.itens.exists.return_value = True
        with self.assertRaises(PedidoCompraError):
            assinar_clinica(pedido, "  ", "127.0.0.1")
