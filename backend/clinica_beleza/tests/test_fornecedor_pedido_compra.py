"""Testes de fornecedor, catálogo e pedido de compra (sem entrada de estoque)."""
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.fornecedor_service import (
    FornecedorError,
    excluir_catalogo,
    excluir_fornecedor,
    importar_catalogo,
    preview_catalogo_arquivo,
    preview_catalogo_pdf,
    _norm_nome,
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
    _montar_pacientes,
    _normalizar_cpf,
    assinar_clinica,
    criar_pedido,
    enviar_pedido_assinado,
    excluir_pedido,
    content_disposition_anexo,
    nome_arquivo_pdf_pedido,
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

    def test_pdf_tabela_phd_ativos_e_codigo(self):
        texto = (
            "MULTI\n"
            "PDRN\n"
            "R$\n"
            "375,50\n"
            "Pdrn + Multiativos\n"
            "CÓDIGO 1719\n"
            "CÓD ATIVOS APL. APRESENT. VALOR\n"
            "501 *5-OH-Triptofano 10mg/2ml - AMP 2ml EV/IM/SC Cx 10 amp. 44,72\n"
            "506 Ácido Hialurônico não reticulado 30mg/2ml - FR 2ml SC/ID Cx 5 fras. 139,78\n"
            "511 Ácido Mandélico 20mg + Ác. Kojico 20mg/ml -\n"
            "AMP 2ml ID Cx 10 amp. 163,71\n"
            "REDUTOR\n"
            "POWER III\n"
            "CÓDIGO 1866\n"
            "235,95\n"
            "+ ZINCO\n"
            "+ PANTOTENATO\n"
            "DE CÁLCIO\n"
            "Cód.: 2009\n"
            "R$ 99,00\n"
            "ZINCO\n"
            "R$ 108,00\n"
        )
        itens = _parse_catalogo_texto_livre(texto)
        por_cod = {i["codigo"]: i for i in itens}
        self.assertIn("1719", por_cod)
        self.assertEqual(por_cod["1719"]["preco_ref"], "375.50")
        self.assertIn("501", por_cod)
        self.assertEqual(por_cod["501"]["preco_ref"], "44.72")
        self.assertIn("5-OH-Triptofano", por_cod["501"]["nome"])
        self.assertIn("506", por_cod)
        self.assertIn("Cx 5", por_cod["506"]["nome"])
        self.assertEqual(por_cod["506"]["preco_ref"], "139.78")
        self.assertIn("511", por_cod)
        self.assertEqual(por_cod["511"]["preco_ref"], "163.71")
        self.assertIn("1866", por_cod)
        self.assertIn("POWER III", por_cod["1866"]["nome"].upper())
        self.assertEqual(por_cod["1866"]["preco_ref"], "235.95")
        nomes = {_norm_nome(i["nome"]) for i in itens}
        self.assertNotIn("zinco", nomes)
        self.assertNotIn("de calcio", nomes)
        self.assertGreaterEqual(len(itens), 5)

    def test_pdf_codigo_sem_preco_ainda_entra_no_catalogo(self):
        """PHD visual: CÓDIGO 216 (skinbooster) vem sem R$ colado no bloco."""
        texto = (
            "HIPERCROMIA PÓS\n"
            "INFLAMATÓRIA\n"
            "4 SESSÕES\n"
            "243,52\n"
            "CÓDIGO 204\n"
            "SKINBOOSTER\n"
            "EFEITO LIFTING\n"
            "Ativos para\n"
            "Aplicação ID\n"
            "CÓDIGO 216\n"
            "Ácido Hialurônico não reticulado 4%/3ml\n"
            "SKINBOOSTER\n"
            "EFEITO LIKE\n"
            "CÓDIGO 217\n"
            "1 SESSÃO\n"
            "116,10\n"
        )
        itens = _parse_catalogo_texto_livre(texto)
        por_cod = {i["codigo"]: i for i in itens}
        self.assertIn("204", por_cod)
        self.assertEqual(por_cod["204"]["preco_ref"], "243.52")
        self.assertIn("216", por_cod)
        self.assertIn("LIFTING", por_cod["216"]["nome"].upper())
        self.assertEqual(por_cod["216"]["preco_ref"], "0.00")
        self.assertIn("217", por_cod)
        self.assertEqual(por_cod["217"]["preco_ref"], "116.10")

    def test_pdf_ignora_ingrediente_solto(self):
        texto = "ZINCO\nR$ 108,00\nDE CÁLCIO\nR$ 99,00\n"
        self.assertEqual(_parse_catalogo_texto_livre(texto), [])


class SalvarFornecedorTests(SimpleTestCase):
    @patch("clinica_beleza.fornecedor_service.existe_documento_duplicado", return_value=True)
    def test_cnpj_duplicado(self, _dup):
        with self.assertRaises(FornecedorError) as ctx:
            salvar_fornecedor(1, {"cnpj": "11.222.333/0001-81", "razao_social": "ACME"})
        self.assertIn("fornecedor", str(ctx.exception).lower())

    def test_cnpj_invalido(self):
        with self.assertRaises(FornecedorError):
            salvar_fornecedor(1, {"cnpj": "123", "razao_social": "ACME"})


class ExcluirFornecedorTests(SimpleTestCase):
    def test_sem_pedido_apaga(self):
        forn = MagicMock()
        forn.pedidos.exists.return_value = False
        self.assertIsNone(excluir_fornecedor(forn))
        forn.delete.assert_called_once()

    def test_com_pedido_desativa(self):
        forn = MagicMock()
        forn.pedidos.exists.return_value = True
        self.assertIs(excluir_fornecedor(forn), forn)
        self.assertFalse(forn.is_active)
        forn.save.assert_called_once()
        forn.delete.assert_not_called()


class ExcluirCatalogoTests(SimpleTestCase):
    def test_apaga_produtos_e_mantem_fornecedor(self):
        forn = MagicMock()
        forn.produtos.all.return_value.delete.return_value = (12, {})
        self.assertEqual(excluir_catalogo(forn), {"removidos": 12})
        forn.produtos.all.return_value.delete.assert_called_once()
        forn.delete.assert_not_called()

    def test_catalogo_vazio(self):
        forn = MagicMock()
        forn.produtos.all.return_value.delete.return_value = (0, {})
        self.assertEqual(excluir_catalogo(forn), {"removidos": 0})
        forn.delete.assert_not_called()


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
        self.assertEqual(res["removidos"], 0)
        self.assertEqual(MockProd.objects.update_or_create.call_count, 2)

    @patch("clinica_beleza.fornecedor_service.excluir_catalogo", return_value={"removidos": 5})
    @patch("clinica_beleza.fornecedor_service.FornecedorProduto")
    def test_substituir_apaga_antes_de_importar(self, MockProd, mock_exc):
        MockProd.objects.update_or_create.return_value = (MagicMock(), True)
        forn = MagicMock(loja_id=1)
        res = importar_catalogo(
            forn,
            [{"codigo": "A", "nome": "Um", "unidade": "un", "preco_ref": "10"}],
            substituir=True,
        )
        mock_exc.assert_called_once_with(forn)
        self.assertEqual(res["removidos"], 5)
        self.assertEqual(res["criados"], 1)
        self.assertEqual(res["atualizados"], 0)


class NomeArquivoPedidoPdfTests(SimpleTestCase):
    def test_usa_nome_fantasia_do_fornecedor(self):
        pedido = MagicMock()
        pedido.numero = 1
        pedido.fornecedor.nome_fantasia = "PHD DO BRASIL"
        pedido.fornecedor.razao_social = "PHD DO BRASIL FARMACIA"
        self.assertEqual(nome_arquivo_pdf_pedido(pedido), "Pedido_01_PHD_DO_BRASIL.pdf")

    def test_cai_na_razao_social(self):
        pedido = MagicMock()
        pedido.numero = 12
        pedido.fornecedor.nome_fantasia = ""
        pedido.fornecedor.razao_social = "Farmácia São José"
        self.assertEqual(nome_arquivo_pdf_pedido(pedido), "Pedido_12_FARMACIA_SAO_JOSE.pdf")

    def test_content_disposition_com_nome_do_fornecedor(self):
        header = content_disposition_anexo("Pedido_01_PHD_DO_BRASIL.pdf")
        self.assertIn('filename="Pedido_01_PHD_DO_BRASIL.pdf"', header)
        self.assertIn("filename*=UTF-8''Pedido_01_PHD_DO_BRASIL.pdf", header)


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
    @patch("clinica_beleza.pedido_compra_service.FornecedorProduto")
    @patch("clinica_beleza.pedido_compra_service.Fornecedor")
    @patch("clinica_beleza.pedido_compra_service.transaction.atomic")
    def test_criar_pedido_nao_altera_estoque(self, mock_atomic, MockForn, MockProd, mock_ped_objs, _Item, mock_mov):
        mock_atomic.return_value = MagicMock(
            __enter__=MagicMock(), __exit__=MagicMock(return_value=False),
        )
        MockForn.objects.filter.return_value.first.return_value = MagicMock(id=1)
        MockProd.objects.filter.return_value.first.return_value = None
        MockProd.objects.create.return_value = MagicMock()
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

    @patch("clinica_beleza.pedido_compra_service.FornecedorProduto")
    def test_item_digitado_grava_no_catalogo(self, MockProd):
        from clinica_beleza.pedido_compra_service import _montar_itens

        forn = MagicMock(id=1, loja_id=9)
        MockProd.objects.filter.return_value.first.return_value = None
        criado = MagicMock()
        MockProd.objects.create.return_value = criado

        montados = _montar_itens(forn, [{
            "codigo": "216",
            "nome": "skinbooster efeito lifting",
            "quantidade": "1",
            "preco": "269.90",
        }])
        MockProd.objects.create.assert_called_once()
        kwargs = MockProd.objects.create.call_args.kwargs
        self.assertEqual(kwargs["codigo"], "216")
        self.assertEqual(kwargs["nome"], "skinbooster efeito lifting")
        self.assertEqual(kwargs["preco_ref"], Decimal("269.90"))
        self.assertIs(montados[0]["catalogo"], criado)

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

    def test_pacientes_opcionais_texto_livre(self):
        self.assertEqual(_normalizar_cpf("12345678901"), "123.456.789-01")
        self.assertEqual(_montar_pacientes(1, []), [])
        self.assertEqual(_montar_pacientes(1, [{"nome": "  ", "cpf": ""}]), [])
        rows = _montar_pacientes(1, [
            {"nome": "Maria Silva", "cpf": "123.456.789-01"},
            {"nome": "Maria Silva", "cpf": "12345678901"},
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nome"], "Maria Silva")
        self.assertEqual(rows[0]["cpf"], "123.456.789-01")
        self.assertIsNone(rows[0]["patient"])


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
        pedido.pacientes.all.return_value = []
        assin_qs = MagicMock()
        assin_qs.filter.side_effect = _assin_filter
        assin_qs.select_related.return_value = assin_qs
        pedido.assinaturas = assin_qs
        return pedido

    @patch("clinica_beleza.prontuario_pdf.header._resolver_cabecalho", return_value=("logo", ""))
    @patch("clinica_beleza.pedido_compra_pdf._watermark_bytes", return_value=None)
    @patch("clinica_beleza.pedido_compra_pdf.logo_image", return_value=None)
    @patch("clinica_beleza.pedido_compra_service._dados_loja")
    def test_pdf_assinado_tem_estrutura_da_proposta(self, mock_loja, _logo, _wm, _cab):
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

    @patch("clinica_beleza.prontuario_pdf.header._resolver_cabecalho", return_value=("logo", ""))
    @patch("clinica_beleza.pedido_compra_pdf.logo_image", return_value=None)
    @patch("clinica_beleza.pedido_compra_service._dados_loja")
    def test_pdf_lista_pacientes(self, mock_loja, _logo, _cab):
        from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra

        mock_loja.return_value = {
            "nome": "Clínica Harmonis",
            "cnpj": "",
            "logo": "",
            "endereco": "",
            "telefone": "",
            "email": "",
        }
        pedido = self._pedido(assinado=False)
        pac = MagicMock()
        pac.nome = "JOANA ALVES"
        pac.cpf = "12345678901"
        pedido.pacientes.all.return_value = [pac]
        pdf = gerar_pdf_pedido_compra(pedido)
        from pypdf import PdfReader
        texto = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("Pacientes", texto)
        self.assertIn("JOANA ALVES", texto)
        self.assertIn("123.456.789-01", texto)

    @patch("clinica_beleza.prontuario_pdf.header._resolver_cabecalho", return_value=("logo", ""))
    @patch("clinica_beleza.pedido_compra_pdf.logo_image", return_value=None)
    @patch("clinica_beleza.pedido_compra_service._dados_loja")
    def test_pdf_codigo_longo_nao_invade_nome(self, mock_loja, _logo, _cab):
        from clinica_beleza.pedido_compra_pdf import gerar_pdf_pedido_compra

        mock_loja.return_value = {
            "nome": "Clínica Harmonis",
            "cnpj": "",
            "logo": "",
            "endereco": "",
            "telefone": "",
            "email": "",
        }
        pedido = self._pedido(assinado=False)
        item = pedido.itens.all.return_value[0]
        item.nome = "ANTIINFLAMATÓRIO E RECUPERATIVO"
        item.codigo = "ANTIINFLAMATORIO-E-RECUPERATIVO"
        pdf = gerar_pdf_pedido_compra(pedido)
        from pypdf import PdfReader
        texto = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("ANTIINFLAMATÓRIO E RECUPERATIVO", texto.replace("\n", " "))
        self.assertIn("ANTIINFLAMATORIO", texto)
        self.assertIn("RECUPERATIVO", texto)
