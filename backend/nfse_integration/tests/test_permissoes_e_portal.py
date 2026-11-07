"""Permissão da nota da loja, host do link e gravação da emissão nacional."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.danfe import url_e_portal_oficial
from nfse_integration.permissoes_loja import pode_acao_nfse


def _user(superuser=False):
    return SimpleNamespace(is_authenticated=True, is_superuser=superuser, id=7)


def _loja(codigo):
    return SimpleNamespace(id=4, owner_id=1, is_active=True, tipo_loja=SimpleNamespace(codigo=codigo))


class PortalOficialTests(SimpleTestCase):
    def test_rejeita_host_que_so_cita_o_dominio(self):
        self.assertFalse(url_e_portal_oficial("https://evil.example/?x=nfse.gov.br"))
        self.assertFalse(url_e_portal_oficial("https://nfse.gov.br.evil.example/x"))
        self.assertFalse(url_e_portal_oficial("https://nota_digital.evil.example/x"))
        self.assertFalse(url_e_portal_oficial("http://nfse.gov.br/"))

    def test_aceita_os_portais_usados(self):
        self.assertTrue(url_e_portal_oficial("https://www.nfse.gov.br/ConsultaPublica/?tpc=1"))
        self.assertTrue(url_e_portal_oficial("https://nfse.issnetonline.com.br/ribeiraopreto/nota"))
        self.assertTrue(url_e_portal_oficial("https://www.notaeletronica.com.br/municipal"))
        self.assertTrue(url_e_portal_oficial("https://www.asaas.com/i/abc"))


class PermissaoNfseLojaTests(SimpleTestCase):
    @patch("core.tenant_access.user_can_access_loja", return_value=True)
    @patch("nfse_integration.permissoes_loja.usuario_admin_nfse", return_value=False)
    def test_clinica_comum_nao_emite_nem_cancela(self, _admin, _acesso):
        loja = _loja("CLIBEL")
        user = _user()
        self.assertFalse(pode_acao_nfse(user, loja, "emitir")[0])
        self.assertFalse(pode_acao_nfse(user, loja, "cancelar")[0])
        self.assertFalse(pode_acao_nfse(user, loja, "salvar_url")[0])
        self.assertTrue(pode_acao_nfse(user, loja, "list")[0])

    @patch("core.tenant_access.user_can_access_loja", return_value=True)
    @patch("nfse_integration.permissoes_loja.usuario_admin_nfse", return_value=False)
    def test_vendedor_comum_emite_e_nao_cancela(self, _admin, _acesso):
        loja = _loja("CRMVND")
        user = _user()
        self.assertTrue(pode_acao_nfse(user, loja, "emitir")[0])
        self.assertFalse(pode_acao_nfse(user, loja, "cancelar")[0])
        self.assertFalse(pode_acao_nfse(user, loja, "destroy")[0])

    @patch("core.tenant_access.user_can_access_loja", return_value=True)
    @patch("nfse_integration.permissoes_loja.usuario_admin_nfse", return_value=True)
    def test_administrador_cancela(self, _admin, _acesso):
        self.assertTrue(pode_acao_nfse(_user(), _loja("CLIBEL"), "emitir")[0])
        self.assertTrue(pode_acao_nfse(_user(), _loja("CRMVND"), "salvar_url")[0])


class GravacaoNacionalTests(SimpleTestCase):
    @patch("nfse_integration.emissao_nacional_loja.salvar_nfse_emitida", return_value=None)
    @patch("nfse_integration.emissao_nacional_loja.gerar_proximo_numero_rps", return_value=8)
    @patch(
        "nfse_integration.emissao_nacional_loja.preparar_endereco_tomador_emissao",
        return_value=({"endereco": "Rua 1"}, None),
    )
    @patch(
        "nfse_integration.emissao_nacional_loja._validar_config_nacional",
        return_value=(b"pfx", "senha", "3540903", "producao"),
    )
    @patch("nfse_integration.nacional.NacionalClient")
    def test_sefin_autorizou_e_o_banco_falhou_nao_e_sucesso(
        self, client_cls, _cfg, _end, _dps, _salvar,
    ):
        from nfse_integration.emissao_nacional_loja import emitir_via_nacional_loja

        client_cls.return_value.emitir_nfse.return_value = {
            "success": True,
            "chave_acesso": "1" * 50,
            "nsu_recepcao": "9",
            "xml_dps": "<NFSe/>",
        }
        email = MagicMock()
        loja = SimpleNamespace(id=6, cpf_cnpj="37302743000126", nome="Harmonis", email="")
        config = SimpleNamespace(aliquota_iss=Decimal("2.00"), inscricao_municipal="")
        resultado = emitir_via_nacional_loja(
            loja,
            config,
            tomador_cpf_cnpj="12345678901",
            tomador_nome="Cliente",
            tomador_email="a@b.c",
            tomador_endereco={"logradouro": "Rua 1"},
            servico_descricao="Detox",
            valor_servicos=Decimal("10.00"),
            enviar_email=True,
            enviar_email_fn=email,
        )
        self.assertFalse(resultado["success"])
        self.assertIn("DPS 8", resultado["error"])
        self.assertNotIn("1" * 50, resultado["error"])
        email.assert_not_called()
