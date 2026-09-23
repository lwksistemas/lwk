"""A foto do recibo precisa ir no corpo do e-mail, não só como anexo."""
from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase

from core.email_delivery import attach_inline_jpeg
from core.resend_api import build_resend_payload


class ResendFotoNoCorpoTest(SimpleTestCase):
    def test_jpeg_inline_vai_com_content_id(self):
        msg = EmailMultiAlternatives(
            subject="Recibo de Pagamento",
            body="Recibo de Pagamento.",
            to=["cliente@example.com"],
        )
        msg.attach_alternative('<img src="cid:recibo" alt="Recibo" />', "text/html")
        attach_inline_jpeg(msg, b"\xff\xd8\xfffoto", cid="recibo", filename="recibo_1.jpg")

        payload = build_resend_payload(msg)

        self.assertIn("cid:recibo", payload["html"])
        self.assertEqual(len(payload["attachments"]), 1)
        anexo = payload["attachments"][0]
        self.assertEqual(anexo["filename"], "recibo_1.jpg")
        self.assertEqual(anexo["content_id"], "recibo")
