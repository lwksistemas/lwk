"""Leitura da chave da NF-e e do retorno da distribuição, sem consultar a SEFAZ."""
import base64
import gzip

from django.test import SimpleTestCase

from clinica_beleza.estoque_nfe_pendente_service import destinatario_confere, numero_da_chave
from clinica_beleza.estoque_nfe_sefaz import (
    SefazNfeErro,
    classificar_documento,
    interpretar_ret_dist,
    xml_evento_ciencia,
)
from clinica_beleza.estoque_xml_import_service import parse_nfe_xml

CHAVE = "35261111111111111111550010000001231000000015"


def _nfe(chave=CHAVE, dest="22222222000191") -> bytes:
    return f"""<?xml version="1.0"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe><infNFe Id="NFe{chave}" versao="4.00">
    <ide><nNF>123</nNF><dhEmi>2026-11-02T10:00:00-03:00</dhEmi></ide>
    <emit><CNPJ>11111111000191</CNPJ><xNome>FORNECEDOR LTDA</xNome></emit>
    <dest><CNPJ>{dest}</CNPJ><xNome>CLINICA</xNome></dest>
    <det nItem="1"><prod>
      <cProd>1</cProd><xProd>TOXINA</xProd><NCM>30029090</NCM>
      <uCom>UN</uCom><qCom>2.00</qCom><vUnCom>10.00</vUnCom><vProd>20.00</vProd>
    </prod></det>
  </infNFe></NFe>
</nfeProc>""".encode()


class NfeEntradaLeituraTests(SimpleTestCase):
    def test_extrai_chave_e_numero(self):
        parsed = parse_nfe_xml(_nfe())
        self.assertEqual(parsed["chave"], CHAVE)
        self.assertEqual(parsed["numero_nota"], "123")
        self.assertEqual(parsed["emitente_documento"], "11111111000191")
        self.assertEqual(numero_da_chave(CHAVE), "123")

    def test_destinatario_so_confere_com_o_mesmo_documento(self):
        self.assertTrue(destinatario_confere("22.222.222/0001-91", "22222222000191"))
        self.assertFalse(destinatario_confere("11111111000191", "22222222000191"))

    def test_resumo_e_xml_completo(self):
        resumo = (
            "<resNFe xmlns='http://www.portalfiscal.inf.br/nfe'>"
            f"<chNFe>{CHAVE}</chNFe><CNPJ>11111111000191</CNPJ>"
            "<xNome>FORNECEDOR</xNome><dhEmi>2026-11-02T10:00:00-03:00</dhEmi>"
            "<tpNF>1</tpNF><vNF>20.00</vNF></resNFe>"
        ).encode()
        info = classificar_documento(resumo)
        self.assertEqual(info["tipo"], "resumo")
        self.assertEqual(info["chave"], CHAVE)
        completo = classificar_documento(_nfe())
        self.assertEqual(completo["tipo"], "completo")
        self.assertEqual(completo["parsed"]["produtos"][0]["nome"], "TOXINA")

    def test_distribuicao_le_o_zip_e_recusa_consumo_indevido(self):
        zipado = base64.b64encode(gzip.compress(
            f"<resNFe xmlns='http://www.portalfiscal.inf.br/nfe'><chNFe>{CHAVE}</chNFe></resNFe>".encode()
        )).decode()
        xml = (
            "<retDistDFeInt xmlns='http://www.portalfiscal.inf.br/nfe'>"
            "<cStat>138</cStat><xMotivo>Documento localizado</xMotivo>"
            "<ultNSU>000000000000010</ultNSU><maxNSU>000000000000010</maxNSU>"
            f"<loteDistDFeInt><docZip NSU='10' schema='resNFe_v1.01.xsd'>{zipado}</docZip></loteDistDFeInt>"
            "</retDistDFeInt>"
        ).encode()
        ret = interpretar_ret_dist(xml)
        self.assertEqual(ret["ult_nsu"], "000000000000010")
        self.assertEqual(len(ret["documentos"]), 1)
        self.assertIn(CHAVE.encode(), ret["documentos"][0]["xml"])

        with self.assertRaises(SefazNfeErro) as ctx:
            interpretar_ret_dist(
                b"<retDistDFeInt><cStat>656</cStat><xMotivo>Consumo indevido</xMotivo>"
                b"<ultNSU>000000000000042</ultNSU><maxNSU>000000000000099</maxNSU></retDistDFeInt>"
            )
        self.assertTrue(ctx.exception.consumo_indevido)
        self.assertEqual(ctx.exception.ult_nsu, "000000000000042")
        self.assertEqual(ctx.exception.max_nsu, "000000000000099")

    def test_evento_de_ciencia_aponta_a_chave(self):
        xml = xml_evento_ciencia(cnpj="22222222000191", chave=CHAVE, homologacao=True)
        self.assertIn("210210", xml)
        self.assertIn(CHAVE, xml)
        self.assertIn("<tpAmb>2</tpAmb>", xml)
