"""Allowlist de URL de PDF da Memed — bloqueia SSRF via pdf_url do cliente."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.memed_prescricao_service import (
    arquivar_pdf_media,
    resolver_pdf_prescricao,
    url_pdf_permitida,
)


class UrlPdfPermitidaTest(SimpleTestCase):
    def test_aceita_memed_e_cdn(self):
        self.assertTrue(url_pdf_permitida("https://cdn.memed.com.br/doc.pdf"))
        self.assertTrue(url_pdf_permitida("https://api.memed.com.br/v1/pdf"))
        self.assertTrue(url_pdf_permitida("https://memed.com.br/receita.pdf"))

    def test_aceita_midia_lwk(self):
        url = "https://media.lwksistemas.com.br/files/41449198000172/paciente/pdf/prescricao.pdf"
        self.assertTrue(url_pdf_permitida(url))

    def test_rejeita_ssrf_e_http(self):
        self.assertFalse(url_pdf_permitida("http://cdn.memed.com.br/doc.pdf"))
        self.assertFalse(url_pdf_permitida("https://127.0.0.1/pdf"))
        self.assertFalse(url_pdf_permitida("https://169.254.169.254/latest/meta-data"))
        self.assertFalse(url_pdf_permitida("https://evil.com/doc.pdf"))
        self.assertFalse(url_pdf_permitida("https://memed.com.br.evil.com/doc.pdf"))
        self.assertFalse(url_pdf_permitida("https://user:pass@cdn.memed.com.br/doc.pdf"))


class ResolverPdfPrescricaoAllowlistTest(SimpleTestCase):
    def test_url_arbitraria_do_frontend_e_ignorada(self):
        with patch(
            "clinica_beleza.memed_prescricao_service.resolver_prescritor_id_profissional",
            return_value=None,
        ):
            url = resolver_pdf_prescricao(
                loja=MagicMock(),
                professional=MagicMock(),
                prescricao_id="abc",
                pdf_url_frontend="https://127.0.0.1/ssrf",
            )
        self.assertEqual(url, "")

    def test_url_memed_do_frontend_e_arquivada(self):
        with patch(
            "clinica_beleza.memed_prescricao_service.arquivar_pdf_media",
            return_value="https://media.lwksistemas.com.br/files/1/a/pdf/p.pdf",
        ) as mock_arq:
            url = resolver_pdf_prescricao(
                loja=MagicMock(),
                professional=MagicMock(),
                prescricao_id="abc",
                pdf_url_frontend="https://cdn.memed.com.br/doc.pdf",
            )
        self.assertTrue(url.startswith("https://media.lwksistemas.com.br/"))
        mock_arq.assert_called_once()


class ArquivarPdfMediaAllowlistTest(SimpleTestCase):
    def test_nao_baixa_url_interna(self):
        with patch("clinica_beleza.memed_prescricao_service.requests.get") as mock_get:
            out = arquivar_pdf_media(MagicMock(), "https://169.254.169.254/x")
        self.assertEqual(out, "")
        mock_get.assert_not_called()
