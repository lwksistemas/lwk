"""Smoke: facade de templates de e-mail pós-split (Fase 21)."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from crm_vendas.assinatura_digital_email_templates import (
    montar_email_cliente_assinatura,
    montar_email_pdf_final,
    montar_email_vendedor_assinatura,
)


class AssinaturaEmailTemplatesSmokeTest(SimpleTestCase):
    def _mocks(self):
        lead = MagicMock()
        lead.nome = "CLIENTE TESTE"
        documento = MagicMock()
        documento.titulo = "Proposta Comercial"
        documento.valor_total = "1.500,00"
        assinatura = MagicMock()
        assinatura.nome_assinante = "VENDEDOR TESTE"
        return lead, documento, assinatura

    def test_montar_email_cliente_retorna_html_e_texto(self):
        lead, documento, _ = self._mocks()
        html, texto = montar_email_cliente_assinatura(
            lead=lead,
            documento=documento,
            loja_nome="Loja Felix",
            link_assinatura="https://example.com/assinar/token",
            tipo_doc="Proposta",
        )
        self.assertIn("CLIENTE TESTE", html)
        self.assertIn("CLIENTE TESTE", texto)
        self.assertIn("Proposta Comercial", html)
        self.assertIn("example.com", texto)

    def test_montar_email_vendedor_retorna_html_e_texto(self):
        lead, documento, assinatura = self._mocks()
        html, texto = montar_email_vendedor_assinatura(
            assinatura=assinatura,
            lead=lead,
            documento=documento,
            loja_nome="Loja Felix",
            link_assinatura="https://example.com/assinar/token",
            tipo_doc="Proposta",
        )
        self.assertIn("VENDEDOR TESTE", html)
        self.assertIn("CLIENTE TESTE", texto)

    def test_montar_email_pdf_final_retorna_html_e_texto(self):
        lead, documento, _ = self._mocks()
        html, texto = montar_email_pdf_final(
            documento=documento,
            lead=lead,
            loja_nome="Loja Felix",
            tipo_doc="Proposta",
        )
        self.assertIn("Documento Assinado", html)
        self.assertIn("pdf assinado digitalmente", texto.lower())
