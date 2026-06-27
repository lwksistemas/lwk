"""Testes — envio síncrono de links de assinatura por WhatsApp."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.assinatura_whatsapp import enviar_whatsapp_link_assinatura
from whatsapp.sync_context import whatsapp_sync_only


class EnviarWhatsappLinkAssinaturaTest(SimpleTestCase):
    @patch('whatsapp.assinatura_whatsapp.whatsapp_envio_permitido', return_value=(True, None))
    @patch('whatsapp.services.send_whatsapp')
    @patch('whatsapp.assinatura_whatsapp._get_whatsapp_config')
    @patch('whatsapp.assinatura_whatsapp._get_loja_nome', return_value='Loja Teste')
    @patch('whatsapp.assinatura_whatsapp._build_link_assinatura', return_value='https://example.com/assinar/x')
    def test_envia_sincrono_sem_enfileirar(self, _mock_link, _mock_loja, mock_config, mock_send, _mock_permitido):
        mock_send.return_value = (True, None)
        config = MagicMock()
        mock_config.return_value = config

        adapter = MagicMock()
        adapter.get_modulo.return_value = 'clinica_beleza'
        adapter.get_destinatario_parte1.return_value = ('Paciente', None)
        adapter.get_titulo.return_value = 'Botox'
        adapter.get_tipo_documento_label.return_value = 'Termo'
        adapter.get_pagina_assinatura_path.return_value = '/assinar-consentimento/'

        documento = MagicMock()
        assinatura = MagicMock(token='tok')

        sync_durante_envio = []

        def capturar_sync(**_kwargs):
            sync_durante_envio.append(whatsapp_sync_only.get())
            return True, None

        mock_send.side_effect = capturar_sync

        ok, err = enviar_whatsapp_link_assinatura(
            adapter,
            documento,
            assinatura,
            loja_id=6,
            telefone='5516981402966',
        )

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(sync_durante_envio, [True])

    @patch('whatsapp.assinatura_whatsapp.whatsapp_envio_permitido', return_value=(True, None))
    @patch('whatsapp.services.send_whatsapp', return_value=(False, 'WhatsApp Web não está conectado.'))
    @patch('whatsapp.assinatura_whatsapp._get_whatsapp_config')
    @patch('whatsapp.assinatura_whatsapp._get_loja_nome', return_value='Loja Teste')
    @patch('whatsapp.assinatura_whatsapp._build_link_assinatura', return_value='https://example.com/assinar/x')
    def test_propaga_erro_real_do_envio(self, _mock_link, _mock_loja, mock_config, _mock_send, _mock_permitido):
        config = MagicMock()
        mock_config.return_value = config

        adapter = MagicMock()
        adapter.get_modulo.return_value = 'clinica_beleza'
        adapter.get_destinatario_parte1.return_value = ('Paciente', None)
        adapter.get_titulo.return_value = 'Botox'
        adapter.get_tipo_documento_label.return_value = 'Termo'
        adapter.get_pagina_assinatura_path.return_value = '/assinar-consentimento/'

        ok, err = enviar_whatsapp_link_assinatura(
            adapter,
            MagicMock(),
            MagicMock(token='tok'),
            loja_id=6,
            telefone='5516981402966',
        )

        self.assertFalse(ok)
        self.assertIn('conectado', err)
