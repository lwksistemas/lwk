"""DANFSe montado a partir do XML da NFS-e Nacional. Não chama o portal."""
from django.test import SimpleTestCase
from pypdf import PdfReader
from io import BytesIO

from nfse_integration.danfse_nacional import gerar_danfse_nacional, ler_dados_danfse

XML = """<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe>
    <xLocEmi>RIBEIRAO PRETO</xLocEmi>
    <xLocPrestacao>RIBEIRAO PRETO</xLocPrestacao>
    <nNFSe>0000000000001</nNFSe>
    <xLocIncid>RIBEIRAO PRETO</xLocIncid>
    <xTribNac>Manutencao de computadores</xTribNac>
    <ambGer>2</ambGer>
    <cStat>100</cStat>
    <dhProc>2026-11-06T14:19:00-03:00</dhProc>
    <emit>
      <CNPJ>24758458000172</CNPJ>
      <xNome>LWK SISTEMAS</xNome>
      <enderNac><xLgr>Rua A</xLgr><nro>10</nro><xBairro>Centro</xBairro><cMun>3543402</cMun><UF>SP</UF><CEP>14000000</CEP></enderNac>
    </emit>
    <valores><vLiq>12.00</vLiq></valores>
    <DPS>
      <infDPS>
        <tpAmb>1</tpAmb>
        <dhEmi>2026-11-06T14:19:15-03:00</dhEmi>
        <serie>1</serie>
        <nDPS>364</nDPS>
        <dCompet>2026-11-06</dCompet>
        <prest><regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN></regTrib></prest>
        <toma>
          <CNPJ>41449198000172</CNPJ>
          <xNome>FELIX REPRESENTACOES</xNome>
          <end><endNac><xLgr>Rua B</xLgr><nro>20</nro><xBairro>Centro</xBairro><UF>SP</UF></endNac></end>
        </toma>
        <serv><cServ><cTribNac>140101</cTribNac><xDescServ>teste</xDescServ></cServ></serv>
        <valores>
          <vServPrest><vServ>12.00</vServ></vServPrest>
          <trib>
            <tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun>
            <totTrib><pTotTribSN>2.00</pTotTribSN></totTrib>
          </trib>
        </valores>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
"""
CHAVE = "35434022224758458000172000000000000126110162861929"


class DanfseNacionalTests(SimpleTestCase):
    def test_le_numero_tomador_e_servico(self):
        dados = ler_dados_danfse(XML, chave=CHAVE)
        self.assertEqual(dados["numero"], "1")
        self.assertEqual(dados["tomador_nome"], "FELIX REPRESENTACOES")
        self.assertEqual(dados["prestador_nome"], "LWK SISTEMAS")
        self.assertEqual(dados["codigo_servico"], "140101")
        self.assertEqual(dados["valor_liquido"], "R$ 12,00")
        self.assertEqual(dados["aliquota_sn"], "2.00%")
        self.assertEqual(dados["ambiente"], "Produção")
        self.assertEqual(dados["gerador"], "Emissor Nacional")
        self.assertEqual(dados["retencao_iss"], "Não retido")

    def test_pdf_e_danfse_com_chave_e_qr(self):
        pdf = gerar_danfse_nacional(XML, chave=CHAVE).getvalue()
        self.assertTrue(pdf.startswith(b"%PDF"))
        texto = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("DANFSe v2.0", texto)
        self.assertIn("PRESTADOR / FORNECEDOR", texto)
        self.assertIn("TOMADOR / ADQUIRENTE", texto)
        self.assertIn("FELIX REPRESENTACOES", texto)
        self.assertIn("Não Retido", texto)
        self.assertIn("R$ 12,00", texto)
        self.assertIn(CHAVE, texto.replace(" ", "").replace("\n", ""))
        self.assertIn("NFS-e Gerada", texto)
        self.assertNotIn("NFS-e CANCELADA", texto)

    def test_pdf_cancelada_mostra_a_situacao(self):
        pdf = gerar_danfse_nacional(XML, chave=CHAVE, cancelada=True).getvalue()
        texto = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("NFS-e Cancelada", texto)
        self.assertIn("NFS-e CANCELADA", texto)
        self.assertNotIn("NFS-e Gerada", texto)
