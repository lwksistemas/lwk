"""Senhas ISSNet cifradas e o webhook global sem detalhe interno."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from core.encryption import (
    cifrar_senhas_issnet_no_mapa,
    cifrar_senhas_issnet_no_objeto,
    decrypt_value,
    encrypt_value,
)


class CifraSenhaIssnetTests(SimpleTestCase):
    def test_mapa_cifra_senha_nova_e_ignora_vazio(self):
        dados = {"issnet_senha": "senha-ws", "issnet_senha_certificado": ""}
        cifrar_senhas_issnet_no_mapa(dados)
        self.assertTrue(dados["issnet_senha"].startswith("enc::"))
        self.assertEqual(decrypt_value(dados["issnet_senha"]), "senha-ws")
        self.assertNotIn("issnet_senha_certificado", dados)

    def test_objeto_cifra_so_o_que_esta_em_texto(self):
        config = SimpleNamespace(
            issnet_senha="texto-puro",
            issnet_senha_certificado=encrypt_value("ja-cifrada"),
        )
        self.assertTrue(cifrar_senhas_issnet_no_objeto(config))
        self.assertEqual(decrypt_value(config.issnet_senha), "texto-puro")
        self.assertEqual(decrypt_value(config.issnet_senha_certificado), "ja-cifrada")
        self.assertFalse(cifrar_senhas_issnet_no_objeto(config))

    def test_cliente_da_loja_le_a_senha_em_claro(self):
        from nfse_integration.issnet_client_factory import issnet_client_loja

        config = SimpleNamespace(
            issnet_ambiente_homologacao=False,
            issnet_certificado=b"pfx",
            issnet_senha_certificado=encrypt_value("abre-pfx"),
            issnet_usuario="prestador",
            issnet_senha=encrypt_value("abre-ws"),
        )
        capturado = {}

        class _Cliente:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def _abrir(**kwargs):
            capturado.update(kwargs)
            return _Cliente()

        with patch("nfse_integration.issnet_client_factory.issnet_client_from_pfx", _abrir):
            with issnet_client_loja(config):
                pass

        self.assertEqual(capturado["senha"], "abre-ws")
        self.assertEqual(capturado["senha_certificado"], "abre-pfx")


@override_settings(WEBHOOK_STRICT_VERIFY=False)
class WebhookGlobalSemDetalheTests(SimpleTestCase):
    def test_erro_interno_nao_volta_na_resposta(self):
        from asaas_integration.views_config.webhook import asaas_webhook

        request = APIRequestFactory().post(
            "/api/asaas/webhook/",
            {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_1"}},
            format="json",
        )
        with (
            patch("core.webhook_security.verify_asaas_access_token", return_value=True),
            patch("asaas_integration.queue_dispatch.should_enqueue_asaas_webhook", return_value=False),
            patch(
                "asaas_integration.webhook_process.process_asaas_global_webhook_sync",
                side_effect=RuntimeError("token-interno-nao-vazar"),
            ),
        ):
            response = asaas_webhook(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("token-interno-nao-vazar", str(response.data))
        self.assertEqual(response.data["message"], "Erro ao processar webhook.")
