"""Prazo do link do recibo e download da logo só na mídia."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.pdf_common.logo import baixar_logo
from clinica_beleza.recibo_assinatura_adapter import ReciboAssinaturaAdapter
from core.assinatura_service import _bloco_titulo_email, decodificar_token, gerar_token


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


def _procedimento(nome, valor):
    linha = MagicMock()
    linha.procedure.nome = nome
    linha.get_valor.return_value = valor
    return linha


class ReciboTituloProcedimentosTest(SimpleTestCase):
    def test_titulo_e_itens_listam_todos_os_procedimentos(self):
        adapter = ReciboAssinaturaAdapter()
        appointment = MagicMock()
        appointment.appointment_procedures.select_related.return_value.all.return_value = [
            _procedimento("DETOX", 300),
            _procedimento("BOTOX — FULL FACE", 700),
        ]
        payment = MagicMock()
        payment.appointment = appointment

        self.assertEqual(adapter.get_titulo(payment), "DETOX · BOTOX — FULL FACE")
        self.assertEqual(
            adapter.get_itens_titulo(payment),
            ["DETOX — R$ 300.00", "BOTOX — FULL FACE — R$ 700.00"],
        )

    def test_email_de_assinatura_lista_cada_procedimento(self):
        html = _bloco_titulo_email(
            "Procedimentos realizados",
            "DETOX · BOTOX — FULL FACE",
            ["DETOX — R$ 300.00", "BOTOX — FULL FACE — R$ 700.00"],
        )
        self.assertIn("DETOX — R$ 300.00", html)
        self.assertIn("BOTOX — FULL FACE — R$ 700.00", html)
        self.assertIn("<br>", html)


class BaixarLogoSsrfTest(SimpleTestCase):
    def test_url_de_fora_nao_dispara_download(self):
        with patch("clinica_beleza.pdf_common.logo.requests.get") as mock_get:
            self.assertIsNone(baixar_logo("https://evil.example/logo.png"))
            self.assertIsNone(baixar_logo("http://127.0.0.1:6379/"))
            mock_get.assert_not_called()
