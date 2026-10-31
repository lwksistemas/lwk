"""A LWK emite assinatura e nota manual pelo ISSNet padrão Nacional (DPS)."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from asaas_integration.nfse_assinatura_service import _emitir_via_issnet
from nfse_integration.emissao_issnet_superadmin import emitir_manual_issnet_superadmin
from nfse_integration.issnet_superadmin import cancelar_nfse_emitida_superadmin


def _config():
    return SimpleNamespace(
        issnet_certificado=b"pfx",
        nacional_certificado=None,
        issnet_senha_certificado="senha",
        nacional_senha_certificado="",
        prestador_cnpj="00000000000191",
        prestador_inscricao_municipal="123",
        prestador_email="nota@lwksistemas.com.br",
        item_lista_servico="14.01",
        codigo_tributacao_municipio="",
        codigo_servico_municipal="140118",
        aliquota_iss=Decimal("2.00"),
        optante_simples_nacional=True,
        nacional_ambiente="producao",
    )


class SuperadminIssnetNacionalTest(SimpleTestCase):
    @patch("asaas_integration.nfse_assinatura_service._enviar_email_nfse_assinatura")
    @patch("asaas_integration.nfse_assinatura_service._salvar_nfse_emitida_issnet")
    @patch("nfse_integration.persistencia_nfse_superadmin.sincronizar_contadores_rps_superadmin")
    @patch("nfse_integration.persistencia_nfse_superadmin.gerar_proximo_numero_rps_superadmin", return_value=41)
    @patch("nfse_integration.issnet_superadmin.issnet_nacional_client_superadmin")
    def test_assinatura_usa_dps(self, client_factory, _proximo, _sync, _salvar, _email):
        client = MagicMock()
        client.emitir_nfse.return_value = {
            "success": True,
            "numero_nfse": "900",
            "chave_acesso": "1" * 50,
            "xml_resposta": "<NFSe/>",
        }
        client_factory.return_value = client

        resultado = _emitir_via_issnet(
            SimpleNamespace(),
            _config(),
            "12345678000199",
            "Cliente",
            "c@loja.com",
            {"codigo_municipio": "3543402"},
            "Licenciamento",
            Decimal("100.00"),
        )

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["serie_rps"], "1")
        self.assertEqual(resultado["codigo_verificacao"], "1" * 50)
        kwargs = client.emitir_nfse.call_args.kwargs
        self.assertEqual(kwargs["serie_dps"], "1")
        self.assertEqual(kwargs["codigo_tributacao_nacional"], "140101")
        self.assertEqual(kwargs["codigo_tributacao_municipal"], "140118")
        self.assertEqual(kwargs["numero_dps"], 41)

    @patch("nfse_integration.emissao_issnet_superadmin.salvar_nfse_emitida_issnet_superadmin")
    @patch("nfse_integration.emissao_issnet_superadmin.sincronizar_contadores_rps_superadmin")
    @patch("nfse_integration.emissao_issnet_superadmin.gerar_proximo_numero_rps_superadmin", return_value=42)
    @patch("nfse_integration.emissao_issnet_superadmin.issnet_nacional_client_superadmin")
    def test_manual_usa_dps(self, client_factory, _proximo, _sync, salvar):
        client = MagicMock()
        client.emitir_nfse.return_value = {
            "success": True,
            "numero_nfse": "901",
            "chave_acesso": "2" * 50,
            "xml_resposta": "<NFSe/>",
        }
        client_factory.return_value = client
        salvar.return_value = SimpleNamespace(id=7)
        payload = SimpleNamespace(
            codigo_servico="",
            tomador_endereco={"codigo_municipio": "3543402"},
            tomador_cpf_cnpj="12345678000199",
            tomador_nome="Cliente",
            tomador_email="c@loja.com",
            descricao="Licenciamento",
            valor=Decimal("80.00"),
        )

        resultado = emitir_manual_issnet_superadmin(_config(), payload)

        self.assertTrue(resultado.success)
        self.assertEqual(client.emitir_nfse.call_args.kwargs["serie_dps"], "1")
        self.assertEqual(salvar.call_args.kwargs["serie_rps"], "1")
        self.assertEqual(salvar.call_args.args[2]["codigo_verificacao"], "2" * 50)

    @patch("nfse_integration.issnet_superadmin.issnet_client_superadmin")
    @patch("nfse_integration.issnet_superadmin.issnet_nacional_client_superadmin")
    def test_cancelamento_de_nota_nova_usa_dps(self, client_factory, client_antigo):
        client = MagicMock()
        client.cancelar_nfse.return_value = {"success": True}
        client_factory.return_value = client
        nf = MagicMock(provedor="issnet", numero_nf="901", codigo_verificacao="3" * 50, xml_nfse="")

        resultado = cancelar_nfse_emitida_superadmin(nf, _config(), "1", "Erro na emissão")

        self.assertTrue(resultado["success"])
        client.cancelar_nfse.assert_called_once()
        self.assertEqual(client.cancelar_nfse.call_args.kwargs["chave_acesso"], "3" * 50)
        client_antigo.assert_not_called()
