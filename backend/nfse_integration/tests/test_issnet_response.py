"""Leitura de XML do ISSNet, sem chamar a prefeitura."""
from django.test import SimpleTestCase

from nfse_integration.issnet_response import (
    extrair_detalhes_nfse_xml,
    extrair_erros,
    interpretar_cancelamento,
    parse_consultar_url_nfse_resposta,
    parse_resposta_cancelamento,
    parse_resposta_xml,
    explicar_recusa_cancelamento,
    mensagem_falha_sincronizacao_nacional,
    resultado_cancelamento_nacional,
)

NS = "http://www.abrasf.org.br/nfse.xsd"


def _nfse(numero="55", codigo="ABC", data="2026-10-12T10:00:00"):
    return f"""
    <ConsultarNfseResposta xmlns="{NS}">
      <CompNfse>
        <Nfse>
          <InfNfse>
            <Numero>{numero}</Numero>
            <CodigoVerificacao>{codigo}</CodigoVerificacao>
            <DataEmissao>{data}</DataEmissao>
            <Servico>
              <Valores>
                <ValorServicos>150.00</ValorServicos>
                <ValorIss>3.00</ValorIss>
                <Aliquota>0.02</Aliquota>
              </Valores>
              <Discriminacao>Consulta</Discriminacao>
            </Servico>
            <TomadorServico>
              <RazaoSocial>Ana</RazaoSocial>
              <IdentificacaoTomador><CpfCnpj><Cnpj>12345678000190</Cnpj></CpfCnpj></IdentificacaoTomador>
            </TomadorServico>
            <IdentificacaoRps><Numero>12</Numero></IdentificacaoRps>
          </InfNfse>
        </Nfse>
      </CompNfse>
    </ConsultarNfseResposta>
    """


class ParseRespostaXmlTests(SimpleTestCase):
    def test_extrai_numero_e_codigo(self):
        out = parse_resposta_xml(_nfse())
        self.assertTrue(out["success"])
        self.assertEqual(out["numero_nf"], "55")
        self.assertEqual(out["codigo_verificacao"], "ABC")

    def test_mensagem_de_erro_e_texto_fora_de_xml(self):
        xml = f"""
        <Retorno xmlns="{NS}">
          <MensagemRetorno>
            <Codigo>E138</Codigo>
            <Mensagem>Nao autorizado</Mensagem>
          </MensagemRetorno>
        </Retorno>
        """
        out = parse_resposta_xml(xml)
        self.assertFalse(out["success"])
        self.assertIn("E138", out["error"])
        self.assertIn("Ribeirao Preto", out["error"])

        fora = parse_resposta_xml("servico indisponivel")
        self.assertFalse(fora["success"])
        self.assertIn("não é XML", fora["error"])


class ConsultaUrlEDetalhesTests(SimpleTestCase):
    def test_url_e_rps(self):
        xml = f"""
        <ConsultarUrlNfseResposta xmlns="{NS}">
          <Links>
            <IdentificacaoNfse><Numero>77</Numero></IdentificacaoNfse>
            <IdentificacaoRps><Numero>12</Numero></IdentificacaoRps>
            <UrlVisualizacaoNfse>https://exemplo/nf</UrlVisualizacaoNfse>
          </Links>
        </ConsultarUrlNfseResposta>
        """
        out = parse_consultar_url_nfse_resposta(xml)
        self.assertTrue(out["success"])
        self.assertEqual(out["numero_nf"], "77")
        self.assertEqual(out["numero_rps"], 12)
        self.assertEqual(out["url"], "https://exemplo/nf")
        self.assertIn("vazia", parse_consultar_url_nfse_resposta("  ")["error"])

    def test_url_nacional_por_ndfse(self):
        xml = """
        <ConsultarUrlNfseResposta xmlns="http://www.sped.fazenda.gov.br/nfse">
          <ListaLinks>
            <Links>
              <IdentificacaoNfse><nDFSe>181</nDFSe></IdentificacaoNfse>
              <UrlVisualizacaoNfse>https://municipal/nota</UrlVisualizacaoNfse>
              <UrlVisualizacaoNfseNacional>https://nacional/nota</UrlVisualizacaoNfseNacional>
            </Links>
          </ListaLinks>
        </ConsultarUrlNfseResposta>
        """
        out = parse_consultar_url_nfse_resposta(xml)
        self.assertTrue(out["success"])
        self.assertEqual(out["numero_nf"], "181")
        self.assertEqual(out["url"], "https://nacional/nota")

    def test_detalhes_do_tomador_e_do_servico(self):
        out = extrair_detalhes_nfse_xml(_nfse())
        self.assertEqual(out["valor"], "150.00")
        self.assertEqual(out["tomador_nome"], "Ana")
        self.assertEqual(out["tomador_cpf_cnpj"], "12345678000190")
        self.assertEqual(out["numero_rps"], 12)
        self.assertEqual(extrair_detalhes_nfse_xml(""), {})


class CancelamentoEErrosTests(SimpleTestCase):
    def test_cancelamento_confirmado_e_motivo_e206(self):
        ok = parse_resposta_cancelamento("<CancelarNfseResposta><DataHoraCancelamento>2026-10-12</DataHoraCancelamento></CancelarNfseResposta>")
        self.assertTrue(ok["success"])

        xml = f"""
        <Retorno xmlns="{NS}">
          <MensagemRetorno>
            <Codigo>E206</Codigo>
            <Mensagem>Erro na emissao</Mensagem>
          </MensagemRetorno>
        </Retorno>
        """
        recusa = parse_resposta_cancelamento(xml)
        self.assertFalse(recusa["success"])
        self.assertIn("substituição", recusa["error"])
        self.assertIn("vazia", parse_resposta_cancelamento("")["error"])

    def test_interpretar_prefere_o_cancelamento_quando_a_nota_nao_veio(self):
        body = "<CancelarNfseResposta></CancelarNfseResposta>"
        out = interpretar_cancelamento(
            {"success": False, "error": "NFS-e nao encontrada na resposta"},
            body,
        )
        self.assertTrue(out["success"])

    def test_extrair_erros_ignora_lista_de_sucesso(self):
        self.assertEqual(extrair_erros("<ListaNfse><Mensagem>ok</Mensagem></ListaNfse>"), "")
        self.assertEqual(extrair_erros("<Mensagem>falhou</Mensagem><Mensagem>de novo</Mensagem>"), "falhou; de novo")
        self.assertEqual(extrair_erros(""), "")

    def test_cancelamento_nacional_so_confirma_com_evento(self):
        recusa = resultado_cancelamento_nacional(
            "<ListaMensagemRetorno><MensagemRetorno>"
            "<Codigo>E160</Codigo><Mensagem>Arquivo em desacordo com o XML Schema.</Mensagem>"
            "<Correcao>Consulte o manual.</Correcao>"
            "</MensagemRetorno></ListaMensagemRetorno>"
        )
        self.assertFalse(recusa["success"])
        self.assertIn("prazo de cancelamento", explicar_recusa_cancelamento(
            "[EM107] Nota aceita. [E0822] Prazo expirou."
        ))
        self.assertIn("já aceitou", explicar_recusa_cancelamento(
            "[EM107] Nota aceita. [E0822] Prazo expirou."
        ))
        self.assertIn("[E160]", explicar_recusa_cancelamento("[E160] Schema."))
        aviso = mensagem_falha_sincronizacao_nacional(
            "Arquivo em desacordo com o XML Schema.",
            "cancelada",
        )
        self.assertIn("não aceitou a consulta", aviso)
        self.assertIn("continua cancelada", aviso)
        self.assertNotIn("Schema", aviso)
        self.assertIn("[E160]", recusa["error"])
        self.assertIn("Consulte o manual.", recusa["error"])

        vazio = resultado_cancelamento_nacional("<CancelarNfseResposta></CancelarNfseResposta>")
        self.assertFalse(vazio["success"])

        ok = resultado_cancelamento_nacional("<RetEvento><cStat>135</cStat><e101103/></RetEvento>")
        self.assertTrue(ok["success"])
        ja = resultado_cancelamento_nacional(
            "<MensagemRetorno><Codigo>EM097</Codigo><Mensagem>NFS-e já está cancelada.</Mensagem></MensagemRetorno>"
        )
        self.assertTrue(ja["success"])
