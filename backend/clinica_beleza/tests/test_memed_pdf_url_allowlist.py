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


class BaixarPdfRedirectAllowlistTest(SimpleTestCase):
    def test_segue_redirect_para_cdn_memed(self):
        from clinica_beleza.memed_prescricao_service import _baixar_pdf_url_permitida

        redirect = MagicMock()
        redirect.status_code = 302
        redirect.headers = {"Location": "https://cdn.memed.com.br/doc.pdf"}
        final = MagicMock()
        final.status_code = 200
        final.content = b"%PDF-1.4 " + (b"x" * 200)
        final.headers = {"Content-Type": "application/pdf"}
        with patch(
            "clinica_beleza.memed_prescricao_service.requests.get",
            side_effect=[redirect, final],
        ):
            pdf = _baixar_pdf_url_permitida("https://api.memed.com.br/v1/doc")
        self.assertIsNotNone(pdf)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_bloqueia_redirect_para_host_interno(self):
        from clinica_beleza.memed_prescricao_service import _baixar_pdf_url_permitida

        redirect = MagicMock()
        redirect.status_code = 302
        redirect.headers = {"Location": "https://127.0.0.1/ssrf"}
        with patch(
            "clinica_beleza.memed_prescricao_service.requests.get",
            return_value=redirect,
        ) as mock_get:
            pdf = _baixar_pdf_url_permitida("https://cdn.memed.com.br/doc.pdf")
        self.assertIsNone(pdf)
        mock_get.assert_called_once()


class CaminhosPdfMemedTest(SimpleTestCase):
    def test_rota_oficial_vem_antes_do_prefixo_sinapse(self):
        from clinica_beleza.memed_prescricao_service import _caminhos_pdf_memed

        caminhos = _caminhos_pdf_memed("https://api.memed.com.br/v1", "295237918")
        self.assertEqual(
            caminhos[0],
            "https://api.memed.com.br/v1/prescricoes/295237918/url-document/full",
        )
        self.assertTrue(any("/sinapse-prescricao/" in c for c in caminhos))


class BuscarPdfUrlMemedTest(SimpleTestCase):
    @patch("clinica_beleza.memed_prescricao_service._obter_token_prescritor", return_value="tok")
    @patch("clinica_beleza.memed_prescricao_service._memed_credentials", return_value=("k", "s"))
    @patch(
        "clinica_beleza.memed_prescricao_service._memed_config",
        return_value=("production", {"api": "https://api.memed.com.br/v1"}),
    )
    def test_usa_url_document_full(self, _cfg, _cred, _token):
        from clinica_beleza.memed_prescricao_service import buscar_pdf_url_memed

        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {
            "data": {"attributes": {"url": "https://cdn.memed.com.br/assinado.pdf"}},
        }
        with patch("clinica_beleza.memed_prescricao_service.requests.get", return_value=resp) as mock_get:
            url = buscar_pdf_url_memed("36971645898", "295237918")
        self.assertEqual(url, "https://cdn.memed.com.br/assinado.pdf")
        chamado = mock_get.call_args[0][0]
        self.assertIn("/prescricoes/295237918/url-document/full", chamado)
        self.assertNotIn("/sinapse-prescricao/", chamado)
