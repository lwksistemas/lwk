"""Testes de fornecedor, catálogo e pedido de compra (sem entrada de estoque)."""
from decimal import Decimal
from io import BytesIO
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
    _fmt_numero,
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
    def test_numero_pedido_com_zero(self):
        self.assertEqual(_fmt_numero(1), "01")
        self.assertEqual(_fmt_numero(12), "12")

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
        pedido.status = PedidoCompra.STATUS_RASCUNHO
        with self.assertRaises(PedidoCompraError) as ctx:
            enviar_pedido_assinado(pedido, ["email"])
        self.assertIn("assin", str(ctx.exception).lower())

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


class PedidoCompraPdfTests(SimpleTestCase):
    def _pedido(self, assinado=True):
        from decimal import Decimal
        from django.utils import timezone

        item = MagicMock()
        item.nome = "Botox 100u"
        item.codigo = "BOTX01"
        item.unidade = "un"
        item.quantidade = Decimal("2")
        item.preco = Decimal("850.00")
        item.subtotal = Decimal("1700.00")

        prof = MagicMock()
        prof.nome = "Ana Souza"
        prof.cpf = "12345678901"
        prof.email = "ana@clinica.com"
        prof.telefone = "16988881111"
        prof.especialidade = "Dermatologia"
        prof.formatar_conselho.return_value = "CRM-SP 12345"

        ass_cli = MagicMock()
        ass_cli.assinado = True
        ass_cli.nome_assinante = "Ana Souza"
        ass_cli.conselho_display = "CRM-SP 12345"
        ass_cli.cpf_assinante = "12345678901"
        ass_cli.email_assinante = "ana@clinica.com"
        ass_cli.ip_address = "10.0.0.1"
        ass_cli.assinado_em = timezone.now()
        ass_cli.profissional = prof

        def _assin_filter(**kwargs):
            qs = MagicMock()
            qs.first.return_value = ass_cli if assinado and kwargs.get("tipo") == "clinica" else None
            return qs

        forn = MagicMock()
        forn.razao_social = "NEXT PHARMA LTDA"
        forn.nome_fantasia = "Next Pharma"
        forn.cnpj = "12.345.678/0001-90"
        forn.telefone = "16999990000"
        forn.email = "vendas@xyz.com"
        forn.logradouro = "Rua A"
        forn.numero = "10"
        forn.complemento = ""
        forn.bairro = "Centro"
        forn.municipio = "Ribeirão Preto"
        forn.uf = "SP"
        forn.cep = "14000-000"

        pedido = MagicMock()
        pedido.loja_id = 1
        pedido.numero = 7
        pedido.valor_total = Decimal("1700.00")
        pedido.observacoes = "Entrega em 5 dias."
        pedido.fornecedor = forn
        pedido.itens.all.return_value = [item]
        assin_qs = MagicMock()
        assin_qs.filter.side_effect = _assin_filter
        assin_qs.select_related.return_value = assin_qs
        pedido.assinaturas = assin_qs
        return pedido

    @patch("clinica_beleza.pedido_compra_pdf._resolver_cabecalho", create=True)
    @patch("clinica_beleza.prontuario_pdf.header._resolver_cabecalho", return_value=("logo", ""))
    @patch("clinica_beleza.pedido_compra_pdf._watermark_bytes", return_value=None)
    @patch("clinica_beleza.pedido_compra_pdf.logo_image", return_value=None)
    @patch("clinica_beleza.pedido_compra_service._dados_loja")
    def test_pdf_assinado_tem_estrutura_da_proposta(self, mock_loja, _logo, _wm, _cab, _cab2):
        from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra

        mock_loja.return_value = {
            "nome": "Clínica Harmonis",
            "cnpj": "37.302.743/0001-26",
            "logo": "",
            "endereco": "Rua X, 100",
            "telefone": "16988880000",
            "email": "contato@harmonis.com",
        }
        pdf = gerar_pdf_pedido_compra(self._pedido(assinado=True))
        self.assertTrue(pdf.startswith(b"%PDF-"))
        from pypdf import PdfReader
        texto = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("PEDIDO DE COMPRA Nº 07", texto)
        self.assertNotIn("Título:", texto)
        self.assertIn("Dados da Empresa", texto)
        self.assertIn("Dados do Fornecedor", texto)
        self.assertIn("Itens do Pedido", texto)
        self.assertIn("Assinatura", texto)
        self.assertIn("123.456.789-01", texto)
        self.assertIn("CRM-SP 12345", texto)
        self.assertIn("Dermatologia", texto)
        self.assertIn("Assinado digitalmente", texto)
        self.assertIn("profissional responsável", texto)

    @patch("clinica_beleza.prontuario_pdf.header._resolver_cabecalho", return_value=("logo", ""))
    @patch("clinica_beleza.pedido_compra_pdf.logo_image", return_value=None)
    @patch("clinica_beleza.pedido_compra_service._dados_loja")
    def test_pdf_rascunho_sem_assinatura_digital(self, mock_loja, _logo, _cab):
        from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra

        mock_loja.return_value = {
            "nome": "Clínica Harmonis",
            "cnpj": "",
            "logo": "",
            "endereco": "",
            "telefone": "",
            "email": "",
        }
        pdf = gerar_pdf_pedido_compra(self._pedido(assinado=False))
        from pypdf import PdfReader
        texto = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("PEDIDO DE COMPRA Nº 07", texto)
        self.assertNotIn("Título:", texto)
        self.assertNotIn("Assinado digitalmente", texto)
