"""Smoke tests: PDF do relatório de comissão."""
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from PIL import Image as PILImage

from crm_vendas.pdf_relatorio_comissao import (
    _build_pdf_cabecalho,
    _fmt_brl,
    _fmt_data,
    gerar_pdf_relatorio_comissao,
)


class FmtRelatorioComissaoTest(SimpleTestCase):
    def test_fmt_brl_positivo(self):
        self.assertEqual(_fmt_brl(Decimal("1234.56")), "R$ 1.234,56")

    def test_fmt_brl_zero(self):
        self.assertEqual(_fmt_brl(0), "R$ 0,00")

    def test_fmt_data_none(self):
        self.assertEqual(_fmt_data(None), "—")


def _mock_relatorio(*, com_detalhe=False):
    ep = MagicMock()
    ep.nome = "Empresa Contratante LTDA"
    ep.cnpj = "12.345.678/0001-90"
    ep.email = "ep@example.com"

    relatorio = MagicMock()
    relatorio.numero = "RC-2026-06"
    relatorio.periodo_descricao = "Junho 2026"
    relatorio.quantidade_vendas = 2
    relatorio.valor_total_vendas = Decimal("10000.00")
    relatorio.valor_total_comissao = Decimal("1500.00")
    relatorio.empresa_prestadora = ep
    relatorio.vendedor = None
    relatorio.dados_oportunidades = (
        [
            {"data": "15/06/2026", "cliente": "Cliente A", "valor": 6000, "comissao": 900},
            {"data": "20/06/2026", "cliente": "Cliente B", "valor": 4000, "comissao": 600},
        ]
        if com_detalhe
        else []
    )
    relatorio.assinatura_vendedor_nome = ""
    relatorio.assinatura_empresa_nome = ""
    relatorio.assinatura_vendedor_em = None
    relatorio.assinatura_empresa_em = None
    return relatorio


def _mock_loja():
    loja = MagicMock()
    loja.id = 1
    loja.nome = "Prestadora CRM"
    loja.cpf_cnpj = "98.765.432/0001-10"
    loja.logo = None
    loja.owner = None
    return loja


class PdfRelatorioComissaoSmokeTest(SimpleTestCase):
    def test_gerar_pdf_sem_detalhamento(self):
        buffer = gerar_pdf_relatorio_comissao(_mock_relatorio(), _mock_loja())
        data = buffer.getvalue()
        self.assertIsInstance(buffer, BytesIO)
        self.assertGreater(len(data), 300)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_gerar_pdf_com_detalhamento_vendas(self):
        buffer = gerar_pdf_relatorio_comissao(
            _mock_relatorio(com_detalhe=True),
            _mock_loja(),
            incluir_assinaturas=False,
        )
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))

    def test_gerar_pdf_com_bloco_assinaturas(self):
        rel = _mock_relatorio()
        rel.assinatura_vendedor_nome = "Vendedor Um"
        rel.assinatura_empresa_nome = "Admin Loja"
        buffer = gerar_pdf_relatorio_comissao(rel, _mock_loja(), incluir_assinaturas=True)
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))

    def test_cabecalho_usa_a_logo_da_prestadora_escolhida(self):
        imagem = BytesIO()
        PILImage.new("RGB", (80, 40), "white").save(imagem, format="PNG")
        resposta = MagicMock(status_code=200, content=imagem.getvalue())
        loja = _mock_loja()
        loja.logo = "https://media.lwksistemas.com.br/files/loja/logo.jpeg"
        relatorio = _mock_relatorio()
        relatorio.empresa_prestadora.logo = "https://media.lwksistemas.com.br/files/prestadora/logo.png"
        with (
            patch("crm_vendas.pdf_proposta_contrato.formatters.requests.get", return_value=resposta),
            patch("core.media_storage.assinar_url_midia", side_effect=lambda url: url) as assinar,
        ):
            elements = _build_pdf_cabecalho(loja, relatorio)
        self.assertEqual(
            [chamada.args[0] for chamada in assinar.call_args_list],
            [loja.logo, relatorio.empresa_prestadora.logo],
        )
        self.assertEqual(len(elements[0]._cellvalues[0]), 3)
