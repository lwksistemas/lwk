"""Token Memed, chave Asaas, webhook e IP do limite público."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIRequestFactory

from clinica_beleza.permissions import login_e_o_prescritor
from clinica_beleza.serializers.nfse_config import ClinicaBelezaNFSeConfigSerializer
from clinica_beleza.throttles import PublicConfirmacaoThrottle, _get_client_ip


class PrescritorMemedTest(SimpleTestCase):
    @patch("clinica_beleza.permissions.professional_id_do_usuario", return_value=4)
    def test_so_o_profissional_do_login(self, _meu):
        request = SimpleNamespace()
        self.assertTrue(login_e_o_prescritor(request, "4"))
        self.assertFalse(login_e_o_prescritor(request, "9"))

    @patch("clinica_beleza.permissions.professional_id_do_usuario", return_value=None)
    def test_dono_sem_vinculo_nao_pede_token_alheio(self, _meu):
        self.assertFalse(login_e_o_prescritor(SimpleNamespace(), "4"))


class ChaveAsaasCriptografadaTest(SimpleTestCase):
    @patch.object(ModelSerializer, "update", return_value="ok")
    def test_grava_com_prefixo_enc(self, mock_update):
        chave = "$aact_hmlg_" + ("a" * 32)
        ClinicaBelezaNFSeConfigSerializer().update(MagicMock(), {"asaas_api_key": chave})
        gravada = mock_update.call_args.args[1]["asaas_api_key"]
        self.assertTrue(gravada.startswith("enc::"))
        self.assertNotIn(chave, gravada)


class WebhookAsaasGetTest(SimpleTestCase):
    @patch("clinica_beleza.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    def test_confirmacao_nao_devolve_id_da_loja(self, mock_resolve):
        mock_resolve.return_value = SimpleNamespace(id=6, slug="clinicaharmonis")
        request = APIRequestFactory().get("/api/clinica-beleza/webhooks/asaas/clinicaharmonis/")
        from clinica_beleza.views_asaas_webhook import clinica_beleza_asaas_webhook

        response = clinica_beleza_asaas_webhook(request, loja_slug="clinicaharmonis")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("loja_id", response.data)
        self.assertTrue(response.data["ok"])


class IpDoLimitePublicoTest(SimpleTestCase):
    def test_ignora_o_endereco_inventado_no_inicio(self):
        request = SimpleNamespace(META={
            "HTTP_X_FORWARDED_FOR": "203.0.113.9, 198.51.100.20",
            "REMOTE_ADDR": "10.0.0.1",
        })
        self.assertEqual(_get_client_ip(request), "198.51.100.20")
        self.assertEqual(PublicConfirmacaoThrottle().get_ident(request), "198.51.100.20")
