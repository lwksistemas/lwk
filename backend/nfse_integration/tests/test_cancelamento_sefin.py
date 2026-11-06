"""Cancelamento da NFS-e Nacional pela Sefin. Não envia evento de verdade."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.issnet_superadmin import cancelar_nfse_emitida_superadmin
from nfse_integration.nacional.cancelamento import construir_xml_cancelamento_sefin
from nfse_integration.nacional.constants import SEFIN_NFSE_URLS
from nfse_integration.nacional.transport import enviar_evento_sefin, interpretar_resposta_evento

CHAVE = "35434022224758458000172000000000000126110162861929"


class XmlCancelamentoSefinTests(SimpleTestCase):
    def test_evento_e_o_cancelamento_direto(self):
        xml = construir_xml_cancelamento_sefin(
            chave_acesso=CHAVE,
            prestador_cnpj="24.758.458/0001-72",
            codigo_cancelamento="2",
            motivo="Serviço não prestado",
        )
        self.assertIn("<e101101>", xml)
        self.assertNotIn("e101103", xml)
        self.assertNotIn("CancelarNfseEnvio", xml)
        self.assertIn(f'Id="PRE{CHAVE}101101"', xml)
        self.assertNotIn("nPedRegEvento", xml)
        self.assertIn("<xDesc>Cancelamento de NFS-e</xDesc>", xml)
        self.assertIn("<cMotivo>2</cMotivo>", xml)
        self.assertIn("<CNPJAutor>24758458000172</CNPJAutor>", xml)

    def test_duplicidade_da_tela_vai_como_outros(self):
        xml = construir_xml_cancelamento_sefin(
            chave_acesso=CHAVE,
            prestador_cnpj="24758458000172",
            codigo_cancelamento="4",
            motivo="Duplicidade da nota",
        )
        self.assertIn("<cMotivo>9</cMotivo>", xml)


class EnvioEventoSefinTests(SimpleTestCase):
    def test_post_vai_para_a_chave_na_sefin(self):
        capturado = {}

        class Resposta:
            status_code = 201
            text = ""

            def json(self):
                return {}

        def post(url, json, **kwargs):
            capturado["url"] = url
            capturado["json"] = json
            return Resposta()

        with patch("nfse_integration.nacional.transport.requests.post", post), patch(
            "nfse_integration.nacional.transport._preparar_cert_mtls",
            return_value=("/tmp/cert.pem", "/tmp/key.pem"),
        ), patch("nfse_integration.nacional.transport._limpar_temp"):
            resposta = enviar_evento_sefin("abc", CHAVE, ambiente="producao", pfx_bytes=b"x", senha_pfx="s")

        self.assertTrue(resposta["success"])
        self.assertEqual(capturado["url"], f"{SEFIN_NFSE_URLS['producao']}/{CHAVE}/eventos")
        self.assertEqual(capturado["json"], {"pedidoRegistroEventoXmlGZipB64": "abc"})

    def test_erro_da_sefin_nao_e_sucesso(self):
        lido = interpretar_resposta_evento({
            "erros": [{"Codigo": "E999", "Descricao": "Evento rejeitado"}],
        })
        self.assertFalse(lido["success"])
        self.assertIn("E999", lido["error"])


class CancelamentoSuperadminNacionalTests(SimpleTestCase):
    def _nota(self):
        nf = MagicMock()
        nf.provedor = "nacional"
        nf.numero_nf = CHAVE
        nf.codigo_verificacao = CHAVE
        nf.numero_rps = 364
        nf.xml_nfse = "<NFSe><nNFSe>1</nNFSe></NFSe>"
        return nf

    @patch("nfse_integration.nacional.cancelamento.cancelar_nfse_sefin", return_value={"success": True})
    def test_sucesso_marca_a_nota_cancelada(self, _envio):
        nf = self._nota()
        resultado = cancelar_nfse_emitida_superadmin(nf, MagicMock(), "2", "Serviço não prestado")
        self.assertTrue(resultado["success"])
        self.assertIn("1", resultado["message"])
        self.assertEqual(nf.status, "cancelada")
        nf.save.assert_called_once()

    @patch(
        "nfse_integration.nacional.cancelamento.cancelar_nfse_sefin",
        return_value={"success": False, "error": "Evento rejeitado"},
    )
    def test_recusa_nao_altera_a_nota(self, _envio):
        nf = self._nota()
        resultado = cancelar_nfse_emitida_superadmin(nf, MagicMock(), "2", "Serviço não prestado")
        self.assertFalse(resultado["success"])
        nf.save.assert_not_called()
