"""O vendedor lê se o WhatsApp da loja está ativo, sem ver a conexão."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.views_config import WhatsAppConfigView


class LeituraWhatsAppVendedorTest(SimpleTestCase):
    def test_vendedor_recebe_o_status_sem_dados_da_conexao(self):
        request = MagicMock()
        loja = MagicMock(id=4)
        config = MagicMock(
            whatsapp_ativo=True,
            enviar_lembrete_24h=True,
            enviar_lembrete_2h=True,
            enviar_lembrete_tarefas=True,
            enviar_proposta_whatsapp=True,
            enviar_contrato_whatsapp=True,
            enviar_termo_consentimento_whatsapp=True,
        )
        view = WhatsAppConfigView()
        with patch("whatsapp.views_config.resolve_loja_from_request", return_value=loja), patch(
            "whatsapp.views_config._user_may_configure_whatsapp", return_value=False,
        ), patch("whatsapp.views_config.config_whatsapp_existente", return_value=config):
            response = view.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["whatsapp_ativo"])
        self.assertNotIn("whatsapp_phone_id", response.data)
        self.assertNotIn("whatsapp_token_set", response.data)
