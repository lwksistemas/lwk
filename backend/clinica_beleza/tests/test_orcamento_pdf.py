from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone
from pypdf import PdfReader

from clinica_beleza.orcamento_service import (
    _build_pdf,
    _observacoes_html_pdf,
    observacoes_para_exibicao,
)


def _orcamento():
    return SimpleNamespace(
        id=7,
        patient=SimpleNamespace(
            nome="Luiz Henrique Felix",
            telefone="16999621823",
            email="financeiroluiz@hotmail.com",
            cpf="222.392.558-89",
        ),
        professional=SimpleNamespace(nome="Nayara da Silva de Souza"),
        observacoes=(
            "Dados do Cliente: SECRETARIA MUNICIPAL Empresa: MUNICIPIO "
            "CPF/CNPJ: 24212862000146 E-mail: foo@bar.com "
            "Dados da empresa: ULTRASIS INFORMÁTICA LTDA. CNPJ 38.900.437/0001-54"
        ),
        valor_total=Decimal("410.00"),
        validade_dias=30,
        created_at=timezone.now(),
    )


def _itens():
    return [
        SimpleNamespace(
            nome_procedimento="MESOTERAPIA CAPILAR",
            quantidade=1,
            valor_customizado=Decimal("280.00"),
            subtotal=Decimal("280.00"),
        ),
        SimpleNamespace(
            nome_procedimento="DEPILAÇÃO A LASER FAIXA DA BARBA",
            quantidade=1,
            valor_customizado=Decimal("130.00"),
            subtotal=Decimal("130.00"),
        ),
    ]


class ObservacoesHtmlPdfTest(SimpleTestCase):
    def test_rotulos_em_negrito(self):
        html_obs = _observacoes_html_pdf(
            "Dados do Cliente: SECRETARIA Empresa: MUNICIPIO CPF/CNPJ: 123 "
            "Dados da empresa: ULTRASIS CNPJ 38.900.437/0001-54 "
            "RUA MARCOS MARKARIAN N 1025",
        )
        self.assertIn("<b>Dados do Cliente:</b>", html_obs)
        self.assertIn("<b>Empresa:</b>", html_obs)
        self.assertIn("<b>CPF/CNPJ:</b>", html_obs)
        self.assertIn("<b>Dados da empresa:</b>", html_obs)
        self.assertIn("<b>CNPJ:</b>", html_obs)
        self.assertIn("<b>Endereço:</b>", html_obs)

    def test_quebra_dados_da_empresa(self):
        out = observacoes_para_exibicao(
            "RIO PARDO Dados da empresa: ULTRASIS INFORMÁTICA LTDA. CNPJ 38.900.437/0001-54",
        )
        self.assertIn("\nDados da empresa:", out)
        self.assertIn("\nCNPJ", out)


class BuildPdfOrcamentoTest(SimpleTestCase):
    @patch("clinica_beleza.pdf_common.watermark.watermark_logo_bytes", return_value=None)
    @patch("clinica_beleza.pdf_common.logo.logo_image", return_value=None)
    def test_gera_pdf_no_visual_do_pedido(self, _logo, _wm):
        pdf = _build_pdf(
            {
                "loja_nome": "Clínica Harmonis",
                "loja_documento": "12.345.678/0001-90",
                "loja_documento_label": "CNPJ",
                "loja_endereco": "Rua X, 100",
                "loja_telefone": "(16) 99962-1823",
                "loja_email": "contato@harmonis.com",
            },
            _orcamento(),
            _itens(),
            com_timbrado=False,
            logo_url="",
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        texto = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("ORÇAMENTO Nº 07", texto)
        self.assertIn("Dados da Clínica", texto)
        self.assertIn("Dados do Paciente", texto)
        self.assertIn("Procedimentos", texto)
        self.assertIn("MESOTERAPIA CAPILAR", texto)
        self.assertIn("410,00", texto)
        self.assertIn("(16) 99962-1823", texto)
        self.assertNotIn("5516999621823", texto)
        self.assertIn("Válido até:", texto)
        self.assertIn("meramente informativo", texto)
