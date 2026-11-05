"""Testes unitários dos helpers de envio de termo de consentimento."""
from unittest import TestCase
from unittest.mock import MagicMock

from types import SimpleNamespace

from clinica_beleza.consentimento_assinatura_envio_service import (
    enviar_whatsapp_profissional,
    normalizar_canal_envio,
    resolver_termos_para_envio,
)
from whatsapp.message_templates import msg_termo_profissional


class ConsentimentoAssinaturaEnvioServiceTest(TestCase):
    def test_sem_telefone_nao_manda_whatsapp_da_profissional(self):
        termo = SimpleNamespace(consulta=SimpleNamespace(professional=SimpleNamespace(telefone="")))
        ok, err = enviar_whatsapp_profissional(
            termo_proc=termo, adapter=None, assinatura=None, loja_id=1,
        )
        self.assertFalse(ok)
        self.assertIn("telefone", err or "")

    def test_mensagem_da_profissional_traz_o_link(self):
        texto = msg_termo_profissional(
            nome="Nayara",
            paciente="Talita",
            procedimento="Preenchimento de mento",
            loja_nome="Harmonis",
            link="https://lwksistemas.com.br/assinar-consentimento/abc",
        )
        self.assertIn("Talita", texto)
        self.assertIn("Preenchimento de mento", texto)
        self.assertIn("https://lwksistemas.com.br/assinar-consentimento/abc", texto)

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
