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

    def test_extrair_detalhes_portal_html(self):
        from nfse_integration.issnet_portal import extrair_detalhes_portal_issnet_html

        html = """
        <table>
          <tr><td>Razão Social</td><td>EMPRESA TESTE LTDA</td></tr>
          <tr><td>CPF/CNPJ</td><td>12.345.678/0001-90</td></tr>
          <tr><td>Valor dos Serviços</td><td>R$ 1.250,00</td></tr>
          <tr><td>Número do RPS</td><td>155</td></tr>
        </table>
        """
        det = extrair_detalhes_portal_issnet_html(html)
        self.assertEqual(det.get('tomador_nome'), 'EMPRESA TESTE LTDA')
        self.assertEqual(det.get('tomador_cpf_cnpj'), '12345678000190')
        self.assertEqual(det.get('valor'), '1250.00')
        self.assertEqual(det.get('numero_rps'), 155)

    def test_nfse_importacao_incompleta(self):
        from types import SimpleNamespace

        from nfse_integration.persistencia_nfse_loja import nfse_importacao_incompleta

        incompleta = SimpleNamespace(
            valor=0,
            tomador_nome='',
            numero_rps=0,
            servico_descricao='Recuperada do ISSNet (consulta por URL)',
        )
        completa = SimpleNamespace(
            valor=100,
            tomador_nome='Cliente',
            numero_rps=155,
            servico_descricao='Serviço prestado',
        )
        self.assertTrue(nfse_importacao_incompleta(incompleta))
        self.assertFalse(nfse_importacao_incompleta(completa))

    def test_construir_xml_consultar_rps_tem_prestador(self):
        from nfse_integration.issnet_xml_builder import construir_xml_consultar_nfse_por_rps

        xml = construir_xml_consultar_nfse_por_rps(
            numero_rps=155,
            serie_rps='1',
            tipo_rps='1',
            prestador_cnpj='41449198000172',
            inscricao_municipal='123456',
        )
        self.assertIn('ConsultarNfseRpsEnvio', xml)
        self.assertIn('<Numero>155</Numero>', xml)
        self.assertIn('41449198000172', xml)
