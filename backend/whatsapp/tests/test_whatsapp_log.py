"""Testes — auditoria WhatsAppLog multi-tenant."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.services import _resolve_whatsapp_log_user_id, _write_whatsapp_log


class ResolveWhatsappLogUserIdTest(SimpleTestCase):
    @patch("django.contrib.auth.get_user_model")
    def test_retorna_none_quando_user_nao_existe_no_schema_da_loja(self, mock_get_user_model):
        User = mock_get_user_model.return_value
        User.objects.using.return_value.filter.return_value.exists.return_value = False
        user = MagicMock(pk=9)

        self.assertIsNone(_resolve_whatsapp_log_user_id("loja_harmonis", user))

    @patch("django.contrib.auth.get_user_model")
    def test_retorna_id_quando_user_existe_no_schema_da_loja(self, mock_get_user_model):
        User = mock_get_user_model.return_value
        User.objects.using.return_value.filter.return_value.exists.return_value = True
        user = MagicMock(pk=9)

        self.assertEqual(_resolve_whatsapp_log_user_id("loja_harmonis", user), 9)


class WriteWhatsappLogTest(SimpleTestCase):
    @patch("whatsapp.services.WhatsAppLog")
    @patch("whatsapp.services._resolve_whatsapp_log_user_id", return_value=None)
    @patch("whatsapp.services._whatsapp_log_db", return_value="loja_test")
    def test_grava_requested_by_user_id_no_response(self, _mock_db, _mock_resolve, mock_log_model):
        user = MagicMock(pk=9)
        mock_log_model.objects.using.return_value.create = MagicMock()

        _write_whatsapp_log(
            loja_id=6,
            telefone="5516981402966",
            mensagem="teste",
            status="falhou",
            response={"error": "evolution_not_connected"},
            user=user,
        )

        kwargs = mock_log_model.objects.using.return_value.create.call_args.kwargs
        self.assertIsNone(kwargs["user_id"])
        self.assertEqual(kwargs["response"]["requested_by_user_id"], 9)
        self.assertEqual(kwargs["response"]["error"], "evolution_not_connected")
