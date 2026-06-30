"""Testes de recuperação NFS-e ISSNet."""

from unittest import TestCase

from nfse_integration.issnet_response import extrair_detalhes_nfse_xml, parse_resposta_xml

SAMPLE_NFSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<CompNfse xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Nfse>
    <InfNfse>
      <Numero>151</Numero>
      <CodigoVerificacao>ABC123</CodigoVerificacao>
      <DataEmissao>2026-06-30T08:30:00</DataEmissao>
      <Servico>
        <Valores>
          <ValorServicos>100.00</ValorServicos>
          <Aliquota>2.00</Aliquota>
          <ValorIss>2.00</ValorIss>
        </Valores>
        <Discriminacao>Servicos de representacao</Discriminacao>
      </Servico>
      <TomadorServico>
        <IdentificacaoTomador>
          <CpfCnpj><Cnpj>24758458000172</Cnpj></CpfCnpj>
        </IdentificacaoTomador>
        <RazaoSocial>LWK SISTEMAS LTDA</RazaoSocial>
      </TomadorServico>
    </InfNfse>
  </Nfse>
</CompNfse>
"""


class IssnetRecuperacaoXmlTest(TestCase):
    def test_parse_resposta_xml_extrai_numero(self):
        parsed = parse_resposta_xml(SAMPLE_NFSE_XML)
        self.assertTrue(parsed.get('success'))
        self.assertEqual(parsed.get('numero_nf'), '151')

    def test_extrair_detalhes_tomador_e_valor(self):
        det = extrair_detalhes_nfse_xml(SAMPLE_NFSE_XML)
        self.assertEqual(det.get('tomador_nome'), 'LWK SISTEMAS LTDA')
        self.assertEqual(det.get('valor'), '100.00')
