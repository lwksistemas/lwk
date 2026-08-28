"""Gateway de parceiro PHP: isolado das lojas LWK."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from superadmin.models import WhatsappInstance
from superadmin.services.whatsapp_painel_service import criar_parceiro, emitir_chave
from whatsapp.evolution_client import _base_url, evolution_target
from whatsapp.parceiro_gateway_service import nome_instancia_parceiro

CPF_OK = "52998224725"
CNPJ_OK = "04252011000110"


class NomeInstanciaParceiroTests(TestCase):
    def test_slug_estavel(self):
        self.assertEqual(nome_instancia_parceiro(7, "Cliente ACME 1"), "ext_7_cliente_acme_1")


class EvolutionTargetTests(TestCase):
    @override_settings(EVOLUTION_API_URL="http://loja-evo", EVOLUTION_PARCEIRO_API_URL="http://parceiro-evo")
    def test_nao_mistura_url_das_lojas(self):
        self.assertEqual(_base_url(), "http://loja-evo")
        with evolution_target("parceiro"):
            self.assertEqual(_base_url(), "http://parceiro-evo")
        self.assertEqual(_base_url(), "http://loja-evo")


class ParceiroGatewayApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("sa-pg@t.com", "sa-pg@t.com", "senha12345")
        self.p = criar_parceiro(nome="PHP Real", documento=CPF_OK, quota_numeros=2)
        _key, self.raw = emitir_chave(self.p, nome="php")
        self.api = APIClient()

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.raw}"}

    def test_me_sem_chave_401(self):
        res = self.api.get("/api/whatsapp/v1/me/")
        self.assertEqual(res.status_code, 401)

    @override_settings(EVOLUTION_PARCEIRO_API_URL="http://wa", EVOLUTION_PARCEIRO_API_KEY="segredo")
    def test_me_com_chave(self):
        res = self.api.get("/api/whatsapp/v1/me/", **self._auth())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["documento"], CPF_OK)
        self.assertTrue(res.data["evolution"])

    @override_settings(EVOLUTION_PARCEIRO_API_URL="http://wa", EVOLUTION_PARCEIRO_API_KEY="segredo")
    def test_nao_acessa_numero_de_outro_parceiro(self):
        outro = criar_parceiro(nome="Outro", documento=CNPJ_OK)
        nome = f"ext_{outro.id}_x"
        WhatsappInstance.objects.create(customer=outro, instance_name=nome, rotulo="x")
        res = self.api.get(f"/api/whatsapp/v1/numeros/{nome}/", **self._auth())
        self.assertEqual(res.status_code, 400)

    @override_settings(EVOLUTION_PARCEIRO_API_URL="", EVOLUTION_PARCEIRO_API_KEY="")
    def test_sem_vm_nao_cria_numero(self):
        res = self.api.post("/api/whatsapp/v1/numeros/", {"cliente_id": "cli1"}, format="json", **self._auth())
        self.assertEqual(res.status_code, 400)

    @override_settings(EVOLUTION_PARCEIRO_API_URL="http://wa", EVOLUTION_PARCEIRO_API_KEY="segredo")
    @patch("whatsapp.parceiro_gateway_service.set_instance_webhook")
    @patch("whatsapp.parceiro_gateway_service.get_connection_state", return_value={"state": "qr_pending", "phone": ""})
    @patch("whatsapp.parceiro_gateway_service.create_evolution_instance_with_qr", return_value={"base64": "data:image/png;base64,AAA"})
    def test_cria_qr_com_cota(self, _qr, _st, _wh):
        res = self.api.post(
            "/api/whatsapp/v1/numeros/",
            {"cliente_id": "loja-a", "rotulo": "Loja A"},
            format="json",
            **self._auth(),
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["instance_name"], f"ext_{self.p.id}_loja_a")
        self.assertTrue(res.data["qr_base64"])

    @override_settings(EVOLUTION_PARCEIRO_API_URL="http://wa", EVOLUTION_PARCEIRO_API_KEY="segredo")
    def test_nao_envia_se_desconectado(self):
        name = f"ext_{self.p.id}_x"
        WhatsappInstance.objects.create(customer=self.p, instance_name=name, status="disconnected")
        with patch(
            "whatsapp.parceiro_gateway_service.get_connection_state",
            return_value={"state": "disconnected", "phone": ""},
        ):
            res = self.api.post(
                "/api/whatsapp/v1/mensagens/",
                {"instance": name, "number": "16999998888", "text": "oi"},
                format="json",
                **self._auth(),
            )
        self.assertEqual(res.status_code, 400)
