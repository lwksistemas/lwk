"""Token Memed, chave Asaas, webhook e IP do limite público."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIRequestFactory

from clinica_beleza.permissions import login_e_o_prescritor
from clinica_beleza.serializers.nfse_config import ClinicaBelezaNFSeConfigSerializer
from clinica_beleza.throttles import PublicConfirmacaoThrottle, _get_client_ip


class DonoComVinculoDeProfissionalTest(SimpleTestCase):
    def test_dona_inicia_a_propria_consulta(self):
        from clinica_beleza.permissions import professional_id_do_usuario, usuario_e_profissional_da_consulta

        loja = SimpleNamespace(owner_id=6)
        user = SimpleNamespace(id=6, is_authenticated=True)
        request = SimpleNamespace(user=user)
        vinculo = SimpleNamespace(professional_id=1)
        consulta = SimpleNamespace(professional_id=1)
        with (
            patch("clinica_beleza.permissions._loja_and_profissional", return_value=(loja, None)),
            patch("clinica_beleza.permissions.ProfissionalUsuario.objects") as objects,
        ):
            objects.filter.return_value.only.return_value.first.return_value = vinculo
            self.assertEqual(professional_id_do_usuario(request), 1)
            self.assertTrue(usuario_e_profissional_da_consulta(request, consulta))

    def test_dona_sem_vinculo_nao_vira_profissional(self):
        from clinica_beleza.permissions import professional_id_do_usuario

        loja = SimpleNamespace(owner_id=6)
        user = SimpleNamespace(id=6, is_authenticated=True)
        request = SimpleNamespace(user=user)
        with (
            patch("clinica_beleza.permissions._loja_and_profissional", return_value=(loja, None)),
            patch("clinica_beleza.permissions.ProfissionalUsuario.objects") as objects,
        ):
            objects.filter.return_value.only.return_value.first.return_value = None
            self.assertIsNone(professional_id_do_usuario(request))


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


class WebhookAsaasTokenDaLojaTest(SimpleTestCase):
    def _post(self):
        return APIRequestFactory().post(
            "/api/clinica-beleza/webhooks/asaas/clinicaharmonis/",
            {"event": "PAYMENT_RECEIVED"},
            format="json",
        )

    @patch("clinica_beleza.views_asaas_webhook._configure_tenant_db_for_loja", return_value=True)
    @patch("clinica_beleza.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    @patch("core.webhook_security.verify_asaas_access_token", return_value=True)
    @patch("clinica_beleza.models.ClinicaBelezaNFSeConfig")
    def test_sem_token_da_loja_nao_aceita_o_global(self, config, verificar, resolver, _tenant):
        resolver.return_value = SimpleNamespace(id=6, slug="clinicaharmonis")
        config.objects.filter.return_value.first.return_value = SimpleNamespace(asaas_webhook_token="")
        from clinica_beleza.views_asaas_webhook import clinica_beleza_asaas_webhook

        response = clinica_beleza_asaas_webhook(self._post(), loja_slug="clinicaharmonis")
        self.assertEqual(response.status_code, 401)
        verificar.assert_not_called()

    @patch("asaas_integration.queue_dispatch.should_enqueue_asaas_webhook", return_value=False)
    @patch("clinica_beleza.asaas_webhook_process.process_asaas_clinica_webhook_sync")
    @patch("clinica_beleza.views_asaas_webhook._configure_tenant_db_for_loja", return_value=True)
    @patch("clinica_beleza.views_asaas_webhook.resolve_loja_from_slug_or_cnpj")
    @patch("core.webhook_security.verify_asaas_access_token", return_value=True)
    @patch("clinica_beleza.models.ClinicaBelezaNFSeConfig")
    def test_confere_o_token_gravado_na_clinica(
        self, config, verificar, resolver, _tenant, _processa, _fila,
    ):
        resolver.return_value = SimpleNamespace(id=6, slug="clinicaharmonis")
        config.objects.filter.return_value.first.return_value = SimpleNamespace(
            asaas_webhook_token="token-da-clinica",
        )
        from clinica_beleza.views_asaas_webhook import clinica_beleza_asaas_webhook

        response = clinica_beleza_asaas_webhook(self._post(), loja_slug="clinicaharmonis")
        self.assertEqual(response.status_code, 200)
        verificar.assert_called_once()
        self.assertEqual(verificar.call_args.kwargs["expected_token"], "token-da-clinica")


class IpDoLimitePublicoTest(SimpleTestCase):
    def test_ignora_o_endereco_inventado_no_inicio(self):
        request = SimpleNamespace(META={
            "HTTP_X_FORWARDED_FOR": "203.0.113.9, 198.51.100.20",
            "REMOTE_ADDR": "10.0.0.1",
        })
        self.assertEqual(_get_client_ip(request), "198.51.100.20")
        self.assertEqual(PublicConfirmacaoThrottle().get_ident(request), "198.51.100.20")
