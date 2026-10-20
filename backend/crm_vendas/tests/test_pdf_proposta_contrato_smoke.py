"""Smoke tests: geração de PDF de proposta e contrato."""
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.pdf_proposta_contrato.generators import gerar_pdf_contrato, gerar_pdf_proposta


def _mock_lead():
    lead = MagicMock()
    lead.nome = "Cliente Teste"
    lead.email = "cliente@example.com"
    lead.telefone = "11999999999"
    lead.logradouro = "Rua A"
    lead.numero = "100"
    lead.complemento = ""
    lead.bairro = "Centro"
    lead.cidade = "São Paulo"
    lead.uf = "SP"
    lead.cep = "01001000"
    return lead


def _mock_oportunidade(*, com_itens=False):
    opp = MagicMock()
    opp.lead = _mock_lead()
    opp.vendedor = None
    itens = MagicMock()
    itens.select_related.return_value.all.return_value = []
    itens.exists.return_value = com_itens
    opp.itens = itens
    return opp


def _mock_proposta():
    proposta = MagicMock()
    proposta.loja_id = 1
    proposta.titulo = "Proposta Comercial XYZ"
    proposta.conteudo = "<p>Escopo do serviço contratado.</p>"
    proposta.desconto_valor = Decimal(0)
    proposta.desconto_percentual = Decimal(0)
    proposta.oportunidade = _mock_oportunidade()
    proposta.status_assinatura = "rascunho"
    return proposta


def _mock_contrato():
    contrato = MagicMock()
    contrato.loja_id = 1
    contrato.numero = "CTR-2026-001"
    contrato.titulo = "Contrato de Prestação"
    contrato.conteudo = "<p>Cláusulas do contrato.</p>"
    contrato.desconto_valor = Decimal(0)
    contrato.desconto_percentual = Decimal(0)
    contrato.oportunidade = _mock_oportunidade()
    contrato.status_assinatura = "rascunho"
    return contrato


@patch(
    "crm_vendas.pdf_proposta_contrato.generators.obter_dados_emitente_documento",
    return_value={"nome": "Loja Teste", "logo": None},
)
@patch("crm_vendas.models.AssinaturaDigital")
class PdfPropostaContratoSmokeTest(SimpleTestCase):
    def test_gerar_pdf_proposta_retorna_bytes_pdf(self, _assin, _loja):
        buffer = gerar_pdf_proposta(_mock_proposta(), incluir_assinaturas=False)
        self.assertIsInstance(buffer, BytesIO)
        data = buffer.getvalue()
        self.assertGreater(len(data), 200)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_gerar_pdf_proposta_com_assinaturas(self, mock_assin, _loja):
        mock_assin.objects.filter.return_value.order_by.return_value = []
        buffer = gerar_pdf_proposta(_mock_proposta(), incluir_assinaturas=True)
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))

    def test_gerar_pdf_contrato_retorna_bytes_pdf(self, _assin, _loja):
        buffer = gerar_pdf_contrato(_mock_contrato(), incluir_assinaturas=False)
        data = buffer.getvalue()
        self.assertGreater(len(data), 200)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_gerar_pdf_contrato_com_assinaturas(self, mock_assin, _loja):
        mock_assin.objects.filter.return_value.order_by.return_value = []
        buffer = gerar_pdf_contrato(_mock_contrato(), incluir_assinaturas=True)
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))

    def test_proposta_sem_loja_id_ainda_gera_pdf(self, _assin, mock_emitente):
        proposta = _mock_proposta()
        proposta.loja_id = None
        proposta.emitente_nome = ""
        mock_emitente.return_value = {}
        buffer = gerar_pdf_proposta(proposta, incluir_assinaturas=False)
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))
        mock_emitente.assert_called_once_with(proposta)

    def test_contrato_sem_itens_ainda_gera_pdf(self, _assin, _loja):
        contrato = _mock_contrato()
        contrato.oportunidade.itens.exists.return_value = False
        buffer = gerar_pdf_contrato(contrato, incluir_assinaturas=False)
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))


class LogoPropostaTest(SimpleTestCase):
    def test_cabecalho_baixa_a_logomarca_com_assinatura(self):
        from PIL import Image as PILImage

        from crm_vendas.pdf_proposta_contrato.sections import _build_cabecalho

        imagem = BytesIO()
        PILImage.new("RGB", (80, 40), "white").save(imagem, format="PNG")
        resposta = MagicMock(status_code=200, content=imagem.getvalue())
        url = "https://media.lwksistemas.com.br/files/41449198000172/loja/logo.jpeg"
        assinada = url + "?e=1&s=abc"
        elements = []
        with (
            patch("crm_vendas.pdf_proposta_contrato.formatters.requests.get", return_value=resposta) as get,
            patch("core.media_storage.assinar_url_midia", return_value=assinada) as assinar,
        ):
            _build_cabecalho(elements, url, "PROPOSTA COMERCIAL")
        assinar.assert_called_once_with(url)
        self.assertEqual(get.call_args.args[0], assinada)
        self.assertEqual(len(elements), 1)

    def test_cabecalho_coloca_as_duas_logos_nas_laterais(self):
        from PIL import Image as PILImage

        from crm_vendas.pdf_proposta_contrato.sections import _build_cabecalho

        imagem = BytesIO()
        PILImage.new("RGB", (80, 40), "white").save(imagem, format="PNG")
        resposta = MagicMock(status_code=200, content=imagem.getvalue())
        principal = "https://media.lwksistemas.com.br/files/41449198000172/loja/logo.jpeg"
        login = "https://media.lwksistemas.com.br/files/41449198000172/loja/login.png"
        elements = []
        with (
            patch("crm_vendas.pdf_proposta_contrato.formatters.requests.get", return_value=resposta),
            patch("core.media_storage.assinar_url_midia", side_effect=lambda url: url + "?e=1&s=abc") as assinar,
        ):
            _build_cabecalho(elements, principal, "PROPOSTA COMERCIAL", login)
        self.assertEqual(assinar.call_count, 2)
        self.assertEqual(len(elements[0]._cellvalues[0]), 3)

    def test_logo_com_margem_branca_fica_da_mesma_altura(self):
        from PIL import Image as PILImage

        from crm_vendas.pdf_proposta_contrato.sections import _build_cabecalho

        justa = BytesIO()
        PILImage.new("RGB", (200, 110), (0, 90, 170)).save(justa, format="PNG")
        com_margem = PILImage.new("RGB", (400, 320), "white")
        com_margem.paste(PILImage.new("RGB", (180, 70), (10, 120, 60)), (110, 120))
        larga = BytesIO()
        com_margem.save(larga, format="JPEG")
        resposta_justa = MagicMock(status_code=200, content=justa.getvalue())
        resposta_larga = MagicMock(status_code=200, content=larga.getvalue())
        elements = []
        with (
            patch(
                "crm_vendas.pdf_proposta_contrato.formatters.requests.get",
                side_effect=[resposta_justa, resposta_larga],
            ),
            patch("core.media_storage.assinar_url_midia", side_effect=lambda url: url),
        ):
            _build_cabecalho(
                elements,
                "https://media.example/a.png",
                "PROPOSTA COMERCIAL",
                "https://media.example/b.jpg",
            )
        esquerda, _titulo, direita = elements[0]._cellvalues[0]
        self.assertAlmostEqual(esquerda.drawHeight, direita.drawHeight, places=2)
