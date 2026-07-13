"""Testes unitários dos helpers de envio de termo de consentimento."""
from unittest import TestCase
from unittest.mock import MagicMock

from clinica_beleza.consentimento_assinatura_envio_service import (
    normalizar_canal_envio,
    resolver_termos_para_envio,
)


class ConsentimentoAssinaturaEnvioServiceTest(TestCase):
    def test_normalizar_canal_envio(self):
        self.assertEqual(normalizar_canal_envio("email"), "email")
        self.assertEqual(normalizar_canal_envio(" WhatsApp "), "whatsapp")
        self.assertIsNone(normalizar_canal_envio("sms"))

    def test_resolver_termos_para_envio_filtra_rascunho(self):
        t1 = MagicMock(status_assinatura_termo="rascunho")
        t2 = MagicMock(status_assinatura_termo="concluido")
        consulta = MagicMock()
        with self.subTest("todos enviados"):
            from unittest.mock import patch

            with patch(
                "clinica_beleza.consentimento_service.garantir_termos_procedimento",
                return_value=[t2],
            ):
                termos, erro = resolver_termos_para_envio(consulta, None)
            self.assertEqual(termos, [])
            self.assertIn("pendentes", erro or "")

        with self.subTest("rascunhos disponíveis"):
            from unittest.mock import patch

            with patch(
                "clinica_beleza.consentimento_service.garantir_termos_procedimento",
                return_value=[t1, t2],
            ):
                termos, erro = resolver_termos_para_envio(consulta, None)
            self.assertEqual(termos, [t1])
            self.assertIsNone(erro)
