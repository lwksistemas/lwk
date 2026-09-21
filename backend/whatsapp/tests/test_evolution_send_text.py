"""Testes — cliente Evolution API."""
from unittest.mock import patch

from django.test import SimpleTestCase

from whatsapp.evolution_client import send_image, send_text


class SendTextEvolutionTest(SimpleTestCase):
    @patch("whatsapp.evolution_client._request", return_value={"key": {"id": "abc"}})
    @patch("whatsapp.evolution_client.resolve_recipient_number", return_value="5516981402966")
    def test_send_text_desativa_link_preview(self, _resolve, mock_request):
        send_text("lwk_loja_6", "5516981402966", "Olá https://lwksistemas.com.br/confirmar/x")

        mock_request.assert_called_once()
        _method, _path, kwargs = mock_request.call_args[0][0], mock_request.call_args[0][1], {}
        if len(mock_request.call_args) > 1:
            kwargs = mock_request.call_args[1]
        body = kwargs.get("json_body") or mock_request.call_args[1].get("json_body")
        self.assertEqual(body["linkPreview"], False)
        self.assertIn("https://lwksistemas.com.br", body["text"])


class SendImageEvolutionTest(SimpleTestCase):
    @patch("whatsapp.evolution_client._request", return_value={"key": {"id": "img1"}})
    @patch("whatsapp.evolution_client.resolve_recipient_number", return_value="5516981402966")
    def test_send_image_usa_mediatype_image(self, _resolve, mock_request):
        send_image(
            "lwk_loja_6",
            "5516981402966",
            "https://api.lwksistemas.com.br/recibo.jpg",
            filename="recibo_118.jpg",
            caption="Recibo de Pagamento",
        )
        body = mock_request.call_args[1]["json_body"]
        self.assertEqual(body["mediatype"], "image")
        self.assertEqual(body["mimetype"], "image/jpeg")
        self.assertEqual(body["fileName"], "recibo_118.jpg")
        self.assertIn("sendMedia", mock_request.call_args[0][1])
