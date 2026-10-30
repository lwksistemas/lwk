"""Cora: o boleto nasce no formato da API e o webhook só ignora aviso incompleto."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from superadmin.cora_client import centavos, documento_cliente, montar_fatura
from superadmin.views.cora import cora_webhook


class CoraFaturaTests(SimpleTestCase):
    def test_valor_em_centavos(self):
        self.assertEqual(centavos("27.83"), 2783)

    def test_documento_sem_pontuacao(self):
        self.assertEqual(documento_cliente("12.345.678/0001-90"), {"identity": "12345678000190", "type": "CNPJ"})

    def test_fatura_traz_boleto_e_pix(self):
        loja = SimpleNamespace(
            nome="Felix",
            cpf_cnpj="123.456.789-09",
            owner=SimpleNamespace(email="loja@exemplo.com"),
            cep="",
            logradouro="",
            numero="",
            bairro="",
            cidade="",
            uf="",
            complemento="",
        )
        corpo = montar_fatura(loja, "49.90", "2026-10-20", "loja_felix_2026-10-20")
        self.assertEqual(corpo["payment_forms"], ["BANK_SLIP", "PIX"])
        self.assertEqual(corpo["services"][0]["amount"], 4990)
        self.assertEqual(corpo["customer"]["document"]["type"], "CPF")
        self.assertNotIn("address", corpo["customer"])

    @override_settings(WEBHOOK_STRICT_VERIFY=True)
    @patch("superadmin.cora_service.confirmar_fatura_paga")
    def test_webhook_sem_fatura_nao_renova(self, confirmar):
        request = APIRequestFactory().post("/api/superadmin/cora-webhook/", {}, format="json")
        response = cora_webhook(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ignored")
        confirmar.assert_not_called()


class CoraWebhookSegredoTests(SimpleTestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    @override_settings(CORA_WEBHOOK_SECRET="segredo-cora")
    @patch("superadmin.cora_service.confirmar_fatura_paga")
    def test_sem_token_nao_consulta_a_fatura(self, confirmar):
        request = APIRequestFactory().post(
            "/api/superadmin/cora-webhook/",
            {},
            format="json",
            HTTP_WEBHOOK_EVENT_TYPE="invoice.paid",
            HTTP_WEBHOOK_RESOURCE_ID="inv_1",
        )
        response = cora_webhook(request)
        self.assertEqual(response.status_code, 401)
        confirmar.assert_not_called()

    @override_settings(CORA_WEBHOOK_SECRET="segredo-cora")
    @patch("superadmin.cora_service.confirmar_fatura_paga", return_value={"success": True})
    def test_token_na_query_segue_o_fluxo(self, confirmar):
        request = APIRequestFactory().post(
            "/api/superadmin/cora-webhook/?token=segredo-cora",
            {},
            format="json",
            HTTP_WEBHOOK_EVENT_TYPE="invoice.paid",
            HTTP_WEBHOOK_RESOURCE_ID="inv_2",
        )
        response = cora_webhook(request)
        self.assertEqual(response.status_code, 200)
        confirmar.assert_called_once_with("inv_2")


class CoraWebhookSemBarraTests(SimpleTestCase):
    def test_aviso_sem_barra_final_nao_pede_login(self):
        response = self.client.post(
            "/api/superadmin/cora-webhook",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ignored")
