"""Testes — envio de link de assinatura por WhatsApp (texto original)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.assinatura_whatsapp import enviar_whatsapp_link_assinatura
from whatsapp.sync_context import whatsapp_sync_only


class EnviarWhatsappLinkAssinaturaTest(SimpleTestCase):
    @patch("whatsapp.assinatura_whatsapp.whatsapp_envio_permitido", return_value=(True, None))
    @patch("whatsapp.services.send_whatsapp")
    @patch("whatsapp.assinatura_whatsapp._get_whatsapp_config")
    @patch("whatsapp.assinatura_whatsapp._get_loja_nome", return_value="Loja Teste")
    @patch("whatsapp.assinatura_whatsapp._build_link_assinatura", return_value="https://example.com/assinar/x")
    def test_envia_texto_sincrono_com_mensagem_original(
        self, _mock_link, _mock_loja, mock_config, mock_send, _mock_envio,
    ):
        mock_send.return_value = (True, None)
        mock_config.return_value = MagicMock()

        adapter = MagicMock()
        adapter.get_modulo.return_value = "clinica_beleza"
        adapter.get_destinatario_parte1.return_value = ("Paciente", None)
        adapter.get_titulo.return_value = "Botox"
        adapter.get_tipo_documento_label.return_value = "Termo de Consentimento Esclarecido"
        adapter.get_pagina_assinatura_path.return_value = "/assinar-consentimento/"

        sync_durante_envio = []

        def capturar(**kwargs):
            sync_durante_envio.append(whatsapp_sync_only.get())
            self.assertIn("*Termo de Consentimento*", kwargs["mensagem"])
            self.assertIn("https://example.com/assinar/x", kwargs["mensagem"])
            self.assertIn("Paciente", kwargs["mensagem"])
            return True, None

        mock_send.side_effect = capturar

        ok, err = enviar_whatsapp_link_assinatura(
            adapter,
            MagicMock(),
            MagicMock(token="tok"),
            loja_id=6,
            telefone="5516981402966",
        )

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(sync_durante_envio, [True])
