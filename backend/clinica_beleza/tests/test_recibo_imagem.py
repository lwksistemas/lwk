"""Recibo enviado como foto (JPEG) no WhatsApp e no e-mail."""
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from clinica_beleza.public_pdf import PREFIX_RECIBO, gravar_pdf_publico, ler_pdf_publico
from clinica_beleza.recibo.imagem import pdf_para_jpeg
from clinica_beleza.recibo.pdf import _gerar_pdf_recibo


class PdfParaJpegTests(SimpleTestCase):
    def _ctx(self):
        return {
            "paciente_nome": "Maria Silva",
            "profissional_nome": "Dra. Ana",
            "loja_nome": "Clínica Estética",
            "loja_cnpj": "12.345.678/0001-90",
            "loja_endereco": "Rua A, 100",
            "loja_telefone": "(11) 99999-0000",
            "loja_email": "contato@clinica.com",
            "procedimentos": [{"nome": "Botox", "valor": 800.0}],
            "taxa_consulta": 200.0,
            "valor_total": 1000.0,
            "valor_pago": 1000.0,
            "desconto": 0.0,
            "metodo": "PIX",
            "data": "21/09/2026 08:00",
            "formas_pagamento": [{"metodo": "PIX", "valor": 1000.0}],
        }

    def test_converte_recibo_pdf_em_jpeg(self):
        pdf = _gerar_pdf_recibo(self._ctx())
        jpeg = pdf_para_jpeg(pdf)
        self.assertTrue(jpeg[:3] == b"\xff\xd8\xff")
        self.assertGreater(len(jpeg), 500)

    def test_rejeita_bytes_que_nao_sao_pdf(self):
        with self.assertRaises(ValueError):
            pdf_para_jpeg(b"nao e pdf")


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ReciboImagemCacheTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_cache_guarda_jpeg_junto_do_pdf(self):
        token = gravar_pdf_publico(
            PREFIX_RECIBO,
            {"payment_id": 118, "pdf": b"%PDF", "imagem": b"\xff\xd8\xfffake"},
        )
        cached = ler_pdf_publico(PREFIX_RECIBO, token)
        self.assertEqual(cached["payment_id"], 118)
        self.assertEqual(cached["imagem"][:3], b"\xff\xd8\xff")


class ReciboAssinadoFotoTests(SimpleTestCase):
    @patch("clinica_beleza.recibo.whatsapp_channel._enviar_recibo_whatsapp", return_value=(True, "ok"))
    @patch("clinica_beleza.recibo.email_channel._enviar_recibo_email", return_value=(True, "ok"))
    def test_depois_de_assinar_usa_o_envio_em_foto(self, mock_email, mock_whatsapp):
        from clinica_beleza.recibo_assinatura_envio_service import enviar_recibo_assinado

        patient = MagicMock()
        appointment = MagicMock()
        payment = MagicMock()
        adapter = MagicMock()
        adapter._patient.return_value = patient
        adapter._appointment.return_value = appointment

        enviar_recibo_assinado(payment=payment, adapter=adapter, loja_id=6)

        mock_email.assert_called_once_with(payment, patient, appointment)
        mock_whatsapp.assert_called_once_with(payment, patient, appointment)
