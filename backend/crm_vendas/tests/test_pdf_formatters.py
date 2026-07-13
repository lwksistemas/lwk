"""Testes de formatação usada nos PDFs de proposta/contrato."""
from django.test import SimpleTestCase

from crm_vendas.pdf_proposta_contrato.formatters import (
    _formatar_endereco_lead,
    _formatar_nome_usuario,
    _formatar_valor,
    _html_to_paragraphs,
    _title_case_endereco,
)


class PdfFormattersTest(SimpleTestCase):
    def test_formatar_valor_monetario(self):
        self.assertEqual(_formatar_valor(1500.5), "R$ 1.500,50")
        self.assertEqual(_formatar_valor(None), "—")

    def test_title_case_endereco_maiusculo(self):
        out = _title_case_endereco("RUA DAS FLORES, CENTRO, SÃO PAULO, SP")
        self.assertIn("Rua", out)
        self.assertIn("SP", out)

    def test_formatar_endereco_lead(self):
        lead = type("Lead", (), {
            "logradouro": "Av Paulista",
            "numero": "1000",
            "complemento": "",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01310100",
        })()
        out = _formatar_endereco_lead(lead)
        self.assertIn("Av Paulista", out)
        self.assertIn("São Paulo/SP", out)

    def test_formatar_nome_usuario(self):
        user = type("User", (), {"first_name": "João", "last_name": "Silva", "username": "js"})()
        self.assertEqual(_formatar_nome_usuario(user), "João Silva")

    def test_html_to_paragraphs_remove_tags(self):
        paras = _html_to_paragraphs("<p>Linha 1</p><p>Linha 2</p>")
        self.assertGreaterEqual(len(paras), 1)
        joined = " ".join(paras)
        self.assertIn("Linha 1", joined)

    def test_html_vazio_retorna_placeholder(self):
        self.assertEqual(_html_to_paragraphs(""), ["Conteúdo não informado."])
