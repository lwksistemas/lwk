"""Testes de fornecedor, catálogo e pedido de compra (sem entrada de estoque)."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.fornecedor_service import (
    FornecedorError,
    importar_catalogo,
    preview_catalogo_arquivo,
    preview_catalogo_pdf,
    _parse_catalogo_texto_livre,
    _texto_pagina_pypdf,
    _texto_parece_planilha,
    salvar_fornecedor,
)
from clinica_beleza.pedido_compra_service import (
    PedidoCompra,
    PedidoCompraError,
    _decimal,
    assinar_clinica,
    criar_pedido,
    enviar_pedido_assinado,
    excluir_pedido,
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

    def test_pdf_catalogo_nome_e_preco(self):
        texto = (
            "BIOESTIMULADOR FACIAL + PDRN\n"
            "Formulação:\n"
            "1 Frasco - Gel\n"
            "Certificado de Garantia\tR$ 373,00\n"
            "PDRN + ÁCIDO HIALURÔNICO\n"
            "Formulação:\n"
            "Anti-Aging com hidratação\n"
            "R$ 217,00\n"
            "KIT BUMBUM UP\n"
            "1 caixa de Bioestimulador Corporal\n"
            "+\n"
            "1 caixa de Mix Atleta\n"
            "R$ 1180,00\n"
            "Certificado de GarantiaR$ 39,00\n"
            "PROCAÍNA 2%\n"
        )
        itens = _parse_catalogo_texto_livre(texto)
        nomes = {i["nome"] for i in itens}
        self.assertIn("BIOESTIMULADOR FACIAL + PDRN", nomes)
        self.assertIn("PDRN + ÁCIDO HIALURÔNICO", nomes)
        self.assertIn("KIT BUMBUM UP", nomes)
        self.assertIn("PROCAÍNA 2%", nomes)
        por_nome = {i["nome"]: i for i in itens}
        self.assertEqual(por_nome["BIOESTIMULADOR FACIAL + PDRN"]["preco_ref"], "373.00")
        self.assertEqual(por_nome["KIT BUMBUM UP"]["preco_ref"], "1180.00")
        self.assertEqual(por_nome["PDRN + ÁCIDO HIALURÔNICO"]["preco_ref"], "217.00")
        self.assertTrue(por_nome["BIOESTIMULADOR FACIAL + PDRN"]["codigo"])

    def test_pdf_vazio_falha(self):
        with self.assertRaises(FornecedorError):
            preview_catalogo_pdf(b"")

    def test_pypdf_usa_extract_padrao_se_layout_vier_vazio(self):
        page = MagicMock()
        page.extract_text.side_effect = lambda *args, **kwargs: (
            "" if kwargs.get("extraction_mode") == "layout" else "BIOESTIMULADOR\nR$ 373,00"
        )
        self.assertIn("BIOESTIMULADOR", _texto_pagina_pypdf(page))

    def test_catalogo_visual_nao_parece_planilha(self):
        texto = (
            "SAÚDE, CIÊNCIA E BELEZA\n"
            "BIOESTIMULADOR FACIAL + PDRN\n"
            "Certificado de Garantia R$ 373,00\n"
        )
        self.assertFalse(_texto_parece_planilha(texto))
        self.assertTrue(_texto_parece_planilha("codigo;nome;preco\nA;Botox;10\n"))
        itens = _parse_catalogo_texto_livre(texto)
        self.assertEqual(itens[0]["nome"], "BIOESTIMULADOR FACIAL + PDRN")
        self.assertEqual(itens[0]["preco_ref"], "373.00")


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
    def test_decimal_br_e_subtotal(self):
        self.assertEqual(_decimal("195,00"), Decimal("195.00"))
        self.assertEqual(_decimal("3") * _decimal("195.00"), Decimal("585.00"))
        self.assertEqual(_decimal("1.195,50"), Decimal("1195.50"))

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

    def test_excluir_pedido_remove_registro(self):
        pedido = MagicMock()
        excluir_pedido(pedido)
        pedido.delete.assert_called_once_with()
