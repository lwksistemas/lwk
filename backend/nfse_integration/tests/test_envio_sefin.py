"""A DPS da NFS-e Nacional sai pela Sefin, não pelo serviço de distribuição."""
import base64
import gzip
from unittest.mock import patch

from decimal import Decimal

from django.test import SimpleTestCase

from nfse_integration.nacional.constants import SEFIN_NFSE_URLS
from nfse_integration.nacional.transport import enviar_dps_sefin, interpretar_resposta_emissao
from nfse_integration.nacional.xml_builder import construir_xml_dps


def _nfse_gzip_b64() -> str:
    xml = b"<NFSe><infNFSe><nNFSe>1</nNFSe></infNFSe></NFSe>"
    return base64.b64encode(gzip.compress(xml)).decode("ascii")


class EnvioSefinTests(SimpleTestCase):
    def test_post_vai_para_sefin_com_dps_gzip(self):
        capturado = {}

        class Resposta:
            status_code = 201
            text = ""

            def json(self):
                return {"chaveAcesso": "1" * 50, "nfseXmlGZipB64": _nfse_gzip_b64()}

        def post(url, json, **kwargs):
            capturado["url"] = url
            capturado["json"] = json
            return Resposta()

        with patch("nfse_integration.nacional.transport.requests.post", post), patch(
            "nfse_integration.nacional.transport._preparar_cert_mtls",
            return_value=("/tmp/cert.pem", "/tmp/key.pem"),
        ), patch("nfse_integration.nacional.transport._limpar_temp"):
            resposta = enviar_dps_sefin(dps_xml_b64="abc", ambiente="producao", pfx_bytes=b"x", senha_pfx="s")

        self.assertTrue(resposta["success"])
        self.assertEqual(capturado["url"], SEFIN_NFSE_URLS["producao"])
        self.assertEqual(capturado["json"], {"dpsXmlGZipB64": "abc"})
        self.assertNotIn("adn.nfse.gov.br", capturado["url"])

    def test_resposta_com_chave_descompacta_a_nota(self):
        lido = interpretar_resposta_emissao({
            "chaveAcesso": "9" * 50,
            "nfseXmlGZipB64": _nfse_gzip_b64(),
            "idDps": "DPS1",
        })
        self.assertTrue(lido["success"])
        self.assertEqual(lido["chave_acesso"], "9" * 50)
        self.assertIn("<nNFSe>1</nNFSe>", lido["xml_nfse"])

    def test_resposta_com_erro_nao_conta_como_emitida(self):
        lido = interpretar_resposta_emissao({
            "erros": [{"Codigo": "E1242", "Descricao": "Tipo DF-e não tratado"}],
        })
        self.assertFalse(lido["success"])
        self.assertIn("E1242", lido["error"])

    def test_codigo_municipal_so_entra_com_tres_digitos(self):
        xml = construir_xml_dps(
            numero_dps=1,
            serie_dps="900",
            codigo_municipio_prestador="3543402",
            prestador_cnpj="24758458000172",
            codigo_servico="140118",
            descricao_servico="teste",
            valor_servicos=Decimal("12.00"),
            optante_simples_nacional=True,
            p_tot_trib_sn=Decimal("2.00"),
        )
        self.assertIn("<cTribNac>140118</cTribNac>", xml)
        self.assertNotIn("cTribMun", xml)
        self.assertIn("<pTotTribSN>2.00</pTotTribSN>", xml)
        self.assertNotIn("indTotTrib", xml)

        com_municipal = construir_xml_dps(
            numero_dps=1,
            serie_dps="900",
            codigo_municipio_prestador="3543402",
            prestador_cnpj="24758458000172",
            codigo_servico="140118",
            codigo_tributacao_municipal="118",
            descricao_servico="teste",
            valor_servicos=Decimal("12.00"),
        )
        self.assertIn("<cTribMun>118</cTribMun>", com_municipal)
