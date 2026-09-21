"""Prazo do link do recibo e download da logo só na mídia."""
from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.pdf_common.logo import baixar_logo
from clinica_beleza.recibo_assinatura_adapter import ReciboAssinaturaAdapter
from core.assinatura_service import decodificar_token, gerar_token


class ReciboLinkPrazoTest(SimpleTestCase):
    def test_prazo_e_duas_horas(self):
        adapter = ReciboAssinaturaAdapter()
        self.assertEqual(adapter.prazo_token(), timedelta(hours=2))
        self.assertIn("2 horas", adapter.aviso_validade_link())

    def test_token_vencido_nao_abre(self):
        token = gerar_token(
            "payment", 1, "paciente", 1,
            modulo="clinica_beleza",
            expiracao=timedelta(seconds=-1),
        )
        self.assertIsNone(decodificar_token(token))

    def test_token_dentro_do_prazo_abre(self):
        token = gerar_token(
            "payment", 1, "paciente", 1,
            modulo="clinica_beleza",
            expiracao=timedelta(hours=2),
        )
        payload = decodificar_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["loja_id"], 1)


class BaixarLogoSsrfTest(SimpleTestCase):
    def test_url_de_fora_nao_dispara_download(self):
        with patch("clinica_beleza.pdf_common.logo.requests.get") as mock_get:
            self.assertIsNone(baixar_logo("https://evil.example/logo.png"))
            self.assertIsNone(baixar_logo("http://127.0.0.1:6379/"))
            mock_get.assert_not_called()
