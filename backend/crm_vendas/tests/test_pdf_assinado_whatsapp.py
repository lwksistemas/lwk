"""O PDF assinado fica disponível para o WhatsApp baixar e é enviado às duas partes."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from crm_vendas.assinatura_pdf_whatsapp import (
    enviar_whatsapp_pdf_assinado,
    nome_arquivo_pdf_assinado,
    telefones_pdf_assinado,
)
from crm_vendas.pdf_publico_whatsapp import gravar_pdf_assinado
from crm_vendas.views_assinatura_publica import DocumentoAssinadoPdfPublicoView


class PdfAssinadoWhatsappTest(SimpleTestCase):
    def test_arquivo_e_telefones_das_duas_partes(self):
        documento = SimpleNamespace(
            id=1,
            titulo="FELIPE COSTA FELIX",
            oportunidade=SimpleNamespace(
                lead=SimpleNamespace(telefone="(16) 98140-2966"),
                vendedor=SimpleNamespace(telefone="16999998888"),
            ),
        )
        self.assertEqual(
            nome_arquivo_pdf_assinado("Proposta", documento),
            "proposta_1_FELIPE_COSTA_FELIX_assinado.pdf",
        )
        self.assertEqual(len(telefones_pdf_assinado(documento)), 2)

    def test_view_publica_devolve_o_pdf(self):
        token = gravar_pdf_assinado(b"%PDF-assinado", "proposta_1_assinado.pdf")
        request = RequestFactory().get(f"/api/crm-vendas/documento-assinado/{token}/")
        response = DocumentoAssinadoPdfPublicoView.as_view()(request, token=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"%PDF-assinado")
        self.assertIn("proposta_1_assinado.pdf", response["Content-Disposition"])

    def test_view_sem_token_responde_404(self):
        request = RequestFactory().get("/api/crm-vendas/documento-assinado/inexistente/")
        response = DocumentoAssinadoPdfPublicoView.as_view()(request, token="inexistente")
        self.assertEqual(response.status_code, 404)
        self.assertIn("não encontrado", json.loads(response.content)["error"])

    @patch("whatsapp.services.send_whatsapp_document", return_value=(True, None))
    @patch("whatsapp.assinatura_whatsapp.whatsapp_envio_permitido", return_value=(True, None))
    @patch("whatsapp.models.WhatsAppConfig")
    @patch("core.public_urls.get_public_api_base_url", return_value="https://api.exemplo.com")
    def test_envio_manda_o_pdf_para_cliente_e_vendedor(self, _base, config, _permitido, enviar):
        config.objects.filter.return_value.first.return_value = object()
        documento = SimpleNamespace(
            id=8,
            titulo="FELIPE COSTA FELIX",
            oportunidade=SimpleNamespace(
                lead=SimpleNamespace(telefone="16981402966"),
                vendedor=SimpleNamespace(telefone="16988887777"),
            ),
        )
        ok, err = enviar_whatsapp_pdf_assinado(documento, 9, b"%PDF", "Proposta")
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(enviar.call_count, 2)
        nomes = {chamada.kwargs["filename"] for chamada in enviar.call_args_list}
        self.assertEqual(nomes, {"proposta_8_FELIPE_COSTA_FELIX_assinado.pdf"})
        self.assertTrue(enviar.call_args.kwargs["document_url"].startswith(
            "https://api.exemplo.com/api/crm-vendas/documento-assinado/",
        ))

    def test_rota_do_pdf_nao_exige_login_da_loja(self):
        from config.security_middleware import SecurityIsolationMiddleware

        caminho = "/api/crm-vendas/documento-assinado/abc/"
        self.assertTrue(SecurityIsolationMiddleware._is_crm_vendas_public_path(caminho))
        self.assertFalse(SecurityIsolationMiddleware(lambda r: None)._is_store_route(caminho))
