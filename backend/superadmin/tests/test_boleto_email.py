"""PDF anexo no e-mail do boleto da assinatura."""
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from superadmin.boleto_email import baixar_pdf_boleto, formatar_valor_boleto


class BoletoEmailTests(SimpleTestCase):
    def test_valor_em_real(self):
        self.assertEqual(formatar_valor_boleto("7"), "R$ 7,00")
        self.assertEqual(formatar_valor_boleto(None), "—")

    def test_recusa_endereco_sem_https(self):
        self.assertEqual(baixar_pdf_boleto("http://banco.example/boleto.pdf"), b"")

    @patch("superadmin.boleto_email.requests.get")
    def test_recusa_arquivo_que_nao_e_pdf(self, get):
        resposta = Mock(status_code=200, url="https://banco.example/boleto", content=b"<html></html>")
        get.return_value = resposta
        self.assertEqual(baixar_pdf_boleto("https://banco.example/boleto"), b"")

    @patch("superadmin.boleto_email.requests.get")
    def test_aceita_pdf(self, get):
        resposta = Mock(status_code=200, url="https://banco.example/boleto.pdf", content=b"%PDF-1.4 ok")
        get.return_value = resposta
        self.assertEqual(baixar_pdf_boleto("https://banco.example/boleto.pdf"), b"%PDF-1.4 ok")
