"""Testes de recuperação NFS-e ISSNet."""

from decimal import Decimal
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

    def test_parse_resposta_xml_lista_por_numero(self):
        xml_lista = """<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoPrestadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
  <ListaNfse>
    <CompNfse>
      <Nfse><InfNfse>
        <Numero>150</Numero>
        <CodigoVerificacao>AAA</CodigoVerificacao>
      </InfNfse></Nfse>
    </CompNfse>
    <CompNfse>
      <Nfse><InfNfse>
        <Numero>151</Numero>
        <CodigoVerificacao>BBB</CodigoVerificacao>
        <Servico><Valores><ValorServicos>2500.00</ValorServicos></Valores>
        <Discriminacao>Servico teste</Discriminacao></Servico>
        <TomadorServico><RazaoSocial>CLIENTE TESTE</RazaoSocial>
        <IdentificacaoTomador><CpfCnpj><Cnpj>24758458000172</Cnpj></CpfCnpj></IdentificacaoTomador>
        </TomadorServico>
      </InfNfse></Nfse>
    </CompNfse>
  </ListaNfse>
</ConsultarNfseServicoPrestadoResposta>"""
        from nfse_integration.issnet_response import parse_resposta_xml_nfse_por_numero

        parsed = parse_resposta_xml_nfse_por_numero(xml_lista, '151')
        self.assertTrue(parsed.get('success'))
        self.assertEqual(parsed.get('numero_nf'), '151')
        det = extrair_detalhes_nfse_xml(parsed.get('xml_nfse', ''))
        self.assertEqual(det.get('tomador_nome'), 'CLIENTE TESTE')
        self.assertEqual(det.get('valor'), '2500.00')

    def test_extrair_detalhes_portal_html(self):
        from nfse_integration.issnet_portal import extrair_detalhes_portal_issnet_html

        html = """
        <div>Prestador CNPJ 41.449.198/0001-72</div>
        <div>Tomador do Serviço</div>
        <table>
          <tr><td>Razão Social</td><td>EMPRESA TESTE LTDA</td></tr>
          <tr><td>CPF/CNPJ</td><td>24.758.458/0001-72</td></tr>
        </table>
        <div>Valor dos Serviços</div><div>R$ 2.500,00</div>
        <div>Número do RPS</div><div>155</div>
        """
        det = extrair_detalhes_portal_issnet_html(html, prestador_cnpj='41449198000172')
        self.assertEqual(det.get('tomador_nome'), 'EMPRESA TESTE LTDA')
        self.assertEqual(det.get('tomador_cpf_cnpj'), '24758458000172')
        self.assertEqual(det.get('valor'), '2500.00')
        self.assertEqual(det.get('numero_rps'), 155)

    def test_extrair_detalhes_portal_span_ids_issnet(self):
        from nfse_integration.issnet_portal import extrair_detalhes_portal_issnet_html

        html = """
        <span id="lblNomeRazaoTomador">LWK SISTEMAS LTDA</span>
        <span id="lblCpfCnpjTomador">24.758.458/0001-72</span>
        <span id="lblValorTotalNota"><b>11,00</b></span>
        <span id="lblValorISS">0,22</span>
        <span id="lblNumRPS">155</span>
        <span id="lblCodigoVerificacao"><b>CA6784EBE</b></span>
        """
        det = extrair_detalhes_portal_issnet_html(html, prestador_cnpj='41449198000172')
        self.assertEqual(det.get('tomador_nome'), 'LWK SISTEMAS LTDA')
        self.assertEqual(det.get('valor'), '11.00')
        self.assertEqual(det.get('numero_rps'), 155)
        self.assertEqual(det.get('codigo_verificacao'), 'CA6784EBE')

    def test_parse_consultar_url_nfse_resposta(self):
        from nfse_integration.issnet_response import parse_consultar_url_nfse_resposta

        xml = """<ConsultarUrlNfseResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
          <ListaLinks>
            <Links>
              <IdentificacaoNfse><Numero>151</Numero></IdentificacaoNfse>
              <IdentificacaoRps><Numero>155</Numero></IdentificacaoRps>
              <UrlVisualizacaoNfse>https://issnet.example/nf151</UrlVisualizacaoNfse>
            </Links>
          </ListaLinks>
        </ConsultarUrlNfseResposta>"""
        parsed = parse_consultar_url_nfse_resposta(xml)
        self.assertTrue(parsed.get('success'))
        self.assertEqual(parsed.get('numero_nf'), '151')
        self.assertEqual(parsed.get('numero_rps'), 155)
        self.assertIn('issnet.example', parsed.get('url', ''))

    def test_nfse_importacao_incompleta(self):
        from types import SimpleNamespace

        from nfse_integration.persistencia_nfse_loja import nfse_importacao_incompleta

        incompleta = SimpleNamespace(
            valor=0,
            tomador_nome='',
            numero_rps=0,
            servico_descricao='Recuperada do ISSNet (consulta por URL)',
            tomador_cpf_cnpj='',
            provedor='issnet',
            status='emitida',
            xml_nfse='',
            xml_rps='',
        )
        incompleta_prest = SimpleNamespace(
            valor=0,
            tomador_nome='',
            numero_rps=0,
            servico_descricao='Recuperada do ISSNet (consulta por URL)',
            tomador_cpf_cnpj='41449198000172',
            provedor='issnet',
            status='emitida',
            xml_nfse='',
            xml_rps='',
        )
        completa = SimpleNamespace(
            valor=100,
            tomador_nome='Cliente',
            numero_rps=155,
            servico_descricao='Serviço prestado',
            tomador_cpf_cnpj='24758458000172',
            provedor='issnet',
            status='emitida',
            xml_nfse='<CompNfse/>',
            xml_rps='',
        )
        sem_xml = SimpleNamespace(
            valor=11,
            tomador_nome='LWK SISTEMAS LTDA',
            numero_rps=155,
            servico_descricao='Serviço',
            tomador_cpf_cnpj='24758458000172',
            provedor='issnet',
            status='emitida',
            xml_nfse='',
            xml_rps='',
        )
        loja = SimpleNamespace(cpf_cnpj='41449198000172')
        self.assertTrue(nfse_importacao_incompleta(incompleta, loja=loja))
        self.assertTrue(nfse_importacao_incompleta(incompleta_prest, loja=loja))
        self.assertFalse(nfse_importacao_incompleta(completa, loja=loja))
        self.assertTrue(nfse_importacao_incompleta(sem_xml, loja=loja))

    def test_gerar_xml_nfse_reconstruido(self):
        from types import SimpleNamespace

        from nfse_integration.xml_nfse_loja import gerar_xml_nfse_reconstruido

        nf = SimpleNamespace(
            numero_nf='151',
            codigo_verificacao='ABC',
            data_emissao=None,
            numero_rps=155,
            valor=Decimal('11.00'),
            valor_iss=Decimal('0.22'),
            aliquota_iss=Decimal('2.00'),
            tomador_cpf_cnpj='24.758.458/0001-72',
            tomador_nome='LWK SISTEMAS LTDA',
            servico_descricao='Servico teste',
        )
        loja = SimpleNamespace(cpf_cnpj='41.449.198/0001-72', inscricao_municipal='20130440', nome='Felix')
        xml = gerar_xml_nfse_reconstruido(nf, loja)
        self.assertIn('<Numero>151</Numero>', xml)
        self.assertIn('LWK SISTEMAS LTDA', xml)
        self.assertIn('<ValorServicos>11.00</ValorServicos>', xml)

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
