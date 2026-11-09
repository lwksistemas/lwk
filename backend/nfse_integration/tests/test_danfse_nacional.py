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
        self.assertEqual(dados["tomador_endereco"], "Rua B, 20, Centro")
        self.assertEqual(dados["tomador_mun_uf"], "SP")

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

    def test_download_da_loja_usa_danfse(self):
        from types import SimpleNamespace

        from nfse_integration.pdf_download import resolver_download_pdf_loja

        nfse = SimpleNamespace(
            provedor="nacional",
            xml_nfse=XML,
            numero_nf="1",
            codigo_verificacao=CHAVE,
            status="emitida",
            id=342,
            pdf_url="",
        )
        resultado = resolver_download_pdf_loja(nfse, SimpleNamespace(), 4)
        self.assertEqual(resultado.tipo, "pdf")
        self.assertEqual(resultado.nome_arquivo, "DANFSe-1.pdf")
        self.assertTrue(resultado.conteudo_pdf.startswith(b"%PDF"))
        texto = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(resultado.conteudo_pdf)).pages)
        self.assertIn("DANFSe v2.0", texto)
        self.assertIn("LWK SISTEMAS", texto)


XML_ENDERECO_NACIONAL = """<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe>
    <xLocEmi>Ribeirão Preto</xLocEmi>
    <nNFSe>2</nNFSe>
    <ambGer>2</ambGer>
    <cStat>100</cStat>
    <dhProc>2026-11-09T08:43:40-03:00</dhProc>
    <emit>
      <CNPJ>41449198000172</CNPJ>
      <xNome>FELIX REPRESENTACOES E COMERCIO LTDA</xNome>
      <enderNac>
        <xLgr>RUA EURIDICE</xLgr><nro>145</nro><xBairro>CENTRO</xBairro>
        <cMun>3543402</cMun><UF>SP</UF><CEP>14057498</CEP>
      </enderNac>
    </emit>
    <valores><vLiq>2500.00</vLiq></valores>
    <DPS>
      <infDPS>
        <tpAmb>1</tpAmb>
        <dhEmi>2026-11-09T00:00:00-03:00</dhEmi>
        <serie>00900</serie>
        <nDPS>192</nDPS>
        <dCompet>2026-11-09</dCompet>
        <toma>
          <CNPJ>38900437000154</CNPJ>
          <xNome>ULTRASIS INFORMATICA LTDA</xNome>
          <end>
            <endNac><cMun>3543402</cMun><CEP>14026583</CEP></endNac>
            <xLgr>Rua Marcos Markarian</xLgr>
            <nro>1025</nro>
            <xCpl>SALA 206</xCpl>
            <xBairro>Nova Alianca</xBairro>
          </end>
          <fone>1636275837</fone>
          <email>karlateixeira1@hotmail.com</email>
        </toma>
        <serv><cServ><cTribNac>140101</cTribNac><xDescServ>Referente ajuda de custos.</xDescServ></cServ></serv>
        <valores><vServPrest><vServ>2500.00</vServ></vServPrest></valores>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
"""


class DanfseTomadorNacionalTests(SimpleTestCase):
    def test_endereco_fora_do_endnac_e_municipio_pelo_ibge(self):
        dados = ler_dados_danfse(XML_ENDERECO_NACIONAL)
        self.assertEqual(
            dados["tomador_endereco"],
            "Rua Marcos Markarian, 1025, SALA 206, Nova Alianca",
        )
        self.assertEqual(dados["tomador_mun_uf"], "Ribeirão Preto / SP")
        self.assertEqual(dados["tomador_ibge_cep"], "3543402 / 14026-583")
        self.assertEqual(dados["tomador_fone"], "(16) 3627-5837")

        pdf = gerar_danfse_nacional(XML_ENDERECO_NACIONAL).getvalue()
        texto = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("Rua Marcos Markarian", texto)
        self.assertIn("Ribeirão Preto / SP", texto)
        self.assertIn("(16) 3627-5837", texto)


class WhatsappDanfseLojaTests(SimpleTestCase):
    def _nfse(self):
        from types import SimpleNamespace

        return SimpleNamespace(
            id=342,
            provedor="nacional",
            status="emitida",
            xml_nfse=XML,
            numero_nf="1",
            codigo_verificacao=CHAVE,
            tomador_nome="LWK SISTEMAS LTDA",
            valor=6,
            servico_descricao="TESTE",
            xml_rps="",
        )

    def test_whatsapp_envia_o_pdf_da_danfse(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from nfse_integration.loja_nfse_api import enviar_whatsapp_nfse_loja

        config = SimpleNamespace(whatsapp_ativo=True)
        with patch("whatsapp.models.WhatsAppConfig.objects") as objects, patch(
            "whatsapp.services.send_whatsapp_document",
            return_value=(True, None),
        ) as enviar, patch(
            "core.public_urls.get_public_api_base_url",
            return_value="https://api.lwksistemas.com.br",
        ):
            objects.filter.return_value.first.return_value = config
            destino = enviar_whatsapp_nfse_loja(
                self._nfse(),
                SimpleNamespace(nome="FELIX REPRESENTACOES E COMERCIO LTDA"),
                4,
                "16999621823",
                SimpleNamespace(user=None),
            )

        self.assertEqual(destino, "16999621823")
        kwargs = enviar.call_args.kwargs
        self.assertEqual(kwargs["filename"], "DANFSe-1.pdf")
        self.assertIn("/api/nfse/documento-pdf/?token=", kwargs["document_url"])
        self.assertIn("NFS-e 1 LWK SISTEMAS LTDA", kwargs["caption"])
        self.assertIn("R$ 6,00", kwargs["caption"])
        self.assertIn("A DANFSe segue em anexo.", kwargs["caption"])
        self.assertNotIn("ConsultaPublica", kwargs["caption"])
        self.assertNotIn("e-mail", kwargs["caption"])
        self.assertNotIn(CHAVE, kwargs["caption"])

    def test_whatsapp_da_nota_cancelada_avisa_a_situacao(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from nfse_integration.loja_nfse_api import enviar_whatsapp_nfse_loja

        nfse = self._nfse()
        nfse.status = "cancelada"
        config = SimpleNamespace(whatsapp_ativo=True)
        with patch("whatsapp.models.WhatsAppConfig.objects") as objects, patch(
            "whatsapp.services.send_whatsapp_document",
            return_value=(True, None),
        ) as enviar, patch(
            "core.public_urls.get_public_api_base_url",
            return_value="https://api.lwksistemas.com.br",
        ):
            objects.filter.return_value.first.return_value = config
            enviar_whatsapp_nfse_loja(
                nfse,
                SimpleNamespace(nome="FELIX REPRESENTACOES E COMERCIO LTDA"),
                4,
                "16999621823",
                SimpleNamespace(user=None),
            )
        self.assertIn("NFS-e cancelada", enviar.call_args.kwargs["caption"])
        self.assertNotIn(CHAVE, enviar.call_args.kwargs["caption"])

    def test_link_publico_entrega_o_pdf(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from django.test import RequestFactory

        from nfse_integration.views_pdf_public import NFSePdfPublicView, criar_token_pdf_nfse

        nfse = self._nfse()
        loja = SimpleNamespace(id=4, database_name="loja_teste", slug="teste")
        token = criar_token_pdf_nfse(342, 4)
        request = RequestFactory().get("/api/nfse/documento-pdf/", {"token": token})
        with patch("superadmin.models.Loja") as loja_model, patch(
            "nfse_integration.views_pdf_public.NFSe.objects"
        ) as objects, patch(
            "nfse_integration.views_pdf_public.ensure_loja_database_config"
        ), patch("nfse_integration.views_pdf_public.set_current_loja_id"), patch(
            "nfse_integration.views_pdf_public.set_current_tenant_db"
        ):
            loja_model.objects.using.return_value.filter.return_value.first.return_value = loja
            objects.filter.return_value.first.return_value = nfse
            response = NFSePdfPublicView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("DANFSe-1.pdf", response["Content-Disposition"])

    def test_superadmin_whatsapp_envia_a_danfse(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from nfse_integration.superadmin_nfse_api import enviar_whatsapp_nfse_superadmin

        nf = SimpleNamespace(
            id=37,
            status="emitida",
            provedor="nacional",
            xml_nfse=XML,
            numero_nf="1",
            codigo_verificacao=CHAVE,
            tomador_nome="FELIX REPRESENTACOES",
            valor=12,
            descricao_servico="teste",
            loja=SimpleNamespace(id=4, database_name="loja_teste", nome="FELIX"),
        )
        config = SimpleNamespace(whatsapp_ativo=True)
        with patch(
            "core.db_config.ensure_loja_database_config",
            return_value=True,
        ), patch("whatsapp.models.WhatsAppConfig.objects") as objects, patch(
            "asaas_integration.models_nfse_config.SuperadminNFSeConfig.get_config",
            return_value=SimpleNamespace(prestador_razao_social="LWK Sistemas"),
        ), patch(
            "whatsapp.services.send_whatsapp_document",
            return_value=(True, None),
        ) as enviar, patch(
            "core.public_urls.get_public_api_base_url",
            return_value="https://api.lwksistemas.com.br",
        ):
            objects.using.return_value.filter.return_value.first.return_value = config
            destino = enviar_whatsapp_nfse_superadmin(
                nf, "16999999999", SimpleNamespace(user=None),
            )

        self.assertEqual(destino, "16999999999")
        kwargs = enviar.call_args.kwargs
        self.assertEqual(kwargs["filename"], "DANFSe-1.pdf")
        self.assertIn("/api/nfse/documento-pdf/?token=", kwargs["document_url"])
        self.assertIn("NFS-e 1 FELIX REPRESENTACOES", kwargs["caption"])
        self.assertIn("LWK Sistemas", kwargs["caption"])
        self.assertNotIn(CHAVE, kwargs["caption"])

    def test_link_publico_da_lwk_entrega_a_danfse(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from django.test import RequestFactory

        from nfse_integration.views_pdf_public import NFSePdfPublicView, criar_token_pdf_nfse_superadmin

        nfse = SimpleNamespace(
            id=37,
            provedor="nacional",
            xml_nfse=XML,
            numero_nf="1",
            codigo_verificacao=CHAVE,
            status="emitida",
            pdf_url="",
            loja=SimpleNamespace(),
        )
        token = criar_token_pdf_nfse_superadmin(37)
        request = RequestFactory().get("/api/nfse/documento-pdf/", {"token": token})
        with patch("superadmin.models.NFSeEmitida") as modelo:
            modelo.objects.select_related.return_value.filter.return_value.first.return_value = nfse
            response = NFSePdfPublicView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("DANFSe-1.pdf", response["Content-Disposition"])
