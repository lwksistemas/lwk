"""Corpo do e-mail da NFS-e e envio simulado. Não dispara SMTP."""
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.email_nfse import (
    enviar_email_nfse_tomador,
    montar_corpo_email_nfse,
    notificar_cancelamento_nfse,
)


class CorpoEmailNfseTests(SimpleTestCase):
    def test_inclui_danfe_e_link_do_xml(self):
        loja = SimpleNamespace(nome="Felix", cpf_cnpj="12.345.678/0001-90")
        corpo = montar_corpo_email_nfse(
            loja=loja,
            tomador_nome="Ana",
            numero_nf="55",
            valor=Decimal("150.5"),
            descricao="Consultoria",
            url_danfe="https://exemplo/NotaDigital.aspx?id=1",
            codigo_verificacao="ABC",
        )
        self.assertIn("Olá Ana", corpo)
        self.assertIn("R$ 150.50", corpo)
        self.assertIn("NotaDigital.aspx", corpo)
        self.assertIn("NotaDigitalXmlDownload.aspx", corpo)
        self.assertIn("ABC", corpo)

    def test_sem_danfe_oferece_a_chave_nacional(self):
        loja = SimpleNamespace(nome="Clínica", cpf_cnpj="")
        corpo = montar_corpo_email_nfse(
            loja=loja,
            tomador_nome="Ana",
            numero_nf="9",
            valor=10,
            descricao="Serviço",
            codigo_verificacao="CHAVE50",
            rodape_simples=True,
            incluir_cnpj_prestador=False,
        )
        self.assertIn("padrão Nacional", corpo)
        self.assertIn("CHAVE50", corpo)
        self.assertIn("notaeletronica.com.br", corpo)
        self.assertNotIn("CNPJ:", corpo)
        self.assertTrue(corpo.endswith("Clínica"))

    def test_chave_do_emissor_nacional_nao_aponta_issnet(self):
        loja = SimpleNamespace(nome="LWK", cpf_cnpj="")
        chave = "35434022224758458000172000000000000126110162861929"
        corpo = montar_corpo_email_nfse(
            loja=loja,
            tomador_nome="FELIX",
            numero_nf="1",
            valor=12,
            descricao="teste",
            codigo_verificacao=chave,
            rodape_simples=True,
            incluir_cnpj_prestador=False,
        )
        self.assertIn("Emissor Nacional", corpo)
        self.assertIn(f"https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave}", corpo)
        self.assertNotIn("notaeletronica.com.br", corpo)
        self.assertIn("Número: 1", corpo)

    def test_link_da_danfse_nao_aponta_a_consulta_publica(self):
        loja = SimpleNamespace(nome="Felix", cpf_cnpj="41.449.198/0001-72")
        corpo = montar_corpo_email_nfse(
            loja=loja,
            tomador_nome="LWK SISTEMAS LTDA",
            numero_nf="1",
            valor=6,
            descricao="TESTE",
            url_danfe="https://api.lwksistemas.com.br/api/nfse/documento-pdf/?token=abc",
            link_e_danfse=True,
            codigo_verificacao="1" * 50,
        )
        self.assertIn("/api/nfse/documento-pdf/?token=abc", corpo)
        self.assertIn("A DANFSe está disponível neste endereço", corpo)
        self.assertNotIn("ConsultaPublica", corpo)
        self.assertNotIn("notaeletronica.com.br", corpo)


class EnvioEmailNfseTests(SimpleTestCase):
    @patch("core.email_delivery.send_prepared")
    @patch("core.email_delivery.create_email_message")
    def test_anexa_o_xml_e_nao_abre_smtp_de_verdade(self, criar, enviar):
        email = MagicMock()
        criar.return_value = email
        loja = SimpleNamespace(nome="Felix", cpf_cnpj="1")
        enviar_email_nfse_tomador(
            loja=loja,
            tomador_email="ana@exemplo.com",
            tomador_nome="Ana",
            numero_nf="55",
            valor=10,
            descricao="Serviço",
            xml_content="<nf/>",
        )
        criar.assert_called_once()
        self.assertIn("55", criar.call_args.kwargs["subject"])
        email.attach.assert_called_once()
        enviar.assert_called_once()

    @patch("nfse_integration.email_nfse.enviar_email_nfse_cancelada_tomador")
    @patch("nfse_integration.danfe.buscar_url_danfe_issnet", return_value="https://exemplo/nota")
    def test_cancelamento_sem_email_nao_envia(self, _danfe, enviar):
        notificar_cancelamento_nfse(
            nfse=SimpleNamespace(tomador_email="  "),
            loja=SimpleNamespace(id=4, nome="Felix"),
        )
        enviar.assert_not_called()

    @patch("nfse_integration.email_nfse.enviar_email_nfse_cancelada_tomador")
    @patch("nfse_integration.danfe.buscar_url_danfe_issnet", return_value="https://exemplo/nota")
    def test_cancelamento_avisa_o_tomador(self, _danfe, enviar):
        notificar_cancelamento_nfse(
            nfse=SimpleNamespace(
                tomador_email="ana@exemplo.com",
                tomador_nome="Ana",
                numero_nf="55",
                servico_descricao="Serviço",
                xml_nfse="<nf/>",
                valor=10,
            ),
            loja=SimpleNamespace(id=4, nome="Felix"),
            loja_id=4,
        )
        enviar.assert_called_once()
        self.assertEqual(enviar.call_args.kwargs["url_danfe"], "https://exemplo/nota")


class ReenvioNacionalSuperadminTests(SimpleTestCase):
    @patch("nfse_integration.danfse_nacional.gerar_danfse_nacional")
    @patch("nfse_integration.email_nfse.enviar_email_nfse_tomador")
    def test_reenvio_usa_numero_curto_empresa_e_pdf(self, enviar, pdf):
        from nfse_integration.superadmin_nfse_api import reenviar_email_nfse_superadmin

        pdf.return_value = BytesIO(b"%PDF")
        config = SimpleNamespace(prestador_razao_social="LWK Sistemas", prestador_cnpj="1")
        nf = SimpleNamespace(
            id=37,
            provedor="nacional",
            tomador_email="ana@exemplo.com",
            tomador_nome="FELIX REPRESENTACOES E COMERCIO LTDA",
            numero_nf="3" * 50,
            codigo_verificacao="3" * 50,
            valor=12,
            descricao_servico="teste",
            xml_nfse="<NFSe xmlns='http://www.sped.fazenda.gov.br/nfse'><nNFSe>000001</nNFSe></NFSe>",
            pdf_url="",
            loja=SimpleNamespace(nome="FELIX", cpf_cnpj="1"),
        )
        reenviar_email_nfse_superadmin(nf, config)
        kwargs = enviar.call_args.kwargs
        self.assertEqual(kwargs["numero_nf"], "1")
        self.assertEqual(kwargs["assunto_prestador"], "FELIX REPRESENTACOES E COMERCIO LTDA")
        self.assertEqual(kwargs["pdf_content"], b"%PDF")
        self.assertEqual(kwargs["pdf_filename"], "DANFSe-1.pdf")
        self.assertEqual(kwargs["xml_filename"], "nfse_1.xml")
        self.assertIn("/api/nfse/documento-pdf/?token=", kwargs["url_danfe"])
        self.assertTrue(kwargs["link_e_danfse"])


class ReenvioNacionalLojaTests(SimpleTestCase):
    @patch("nfse_integration.danfse_nacional.gerar_danfse_nacional")
    @patch("nfse_integration.email_nfse.enviar_email_nfse_tomador")
    def test_reenvio_anexa_danfse_e_nao_usa_portal_issnet(self, enviar, pdf):
        from nfse_integration.loja_nfse_api import reenviar_email_nfse_loja

        pdf.return_value = BytesIO(b"%PDF")
        nf = SimpleNamespace(
            id=342,
            provedor="nacional",
            status="emitida",
            tomador_email="financeiro@exemplo.com",
            tomador_nome="LWK SISTEMAS LTDA",
            numero_nf="1",
            codigo_verificacao="4" * 50,
            valor=6,
            servico_descricao="TESTE",
            xml_nfse="<NFSe/>",
            xml_rps="",
        )
        loja = SimpleNamespace(id=4, nome="FELIX REPRESENTACOES")
        reenviar_email_nfse_loja(nf, loja, 4)
        kwargs = enviar.call_args.kwargs
        self.assertEqual(kwargs["numero_nf"], "1")
        self.assertEqual(kwargs["assunto_prestador"], "LWK SISTEMAS LTDA")
        self.assertEqual(kwargs["pdf_filename"], "DANFSe-1.pdf")
        self.assertEqual(kwargs["pdf_content"], b"%PDF")
        self.assertEqual(kwargs["xml_filename"], "nfse_1.xml")
        self.assertIn("/api/nfse/documento-pdf/?token=", kwargs["url_danfe"])
        self.assertNotIn("ConsultaPublica", kwargs["url_danfe"])
        self.assertTrue(kwargs["link_e_danfse"])
