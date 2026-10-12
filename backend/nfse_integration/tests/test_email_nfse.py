"""Corpo do e-mail da NFS-e e envio simulado. Não dispara SMTP."""
from decimal import Decimal
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
        self.assertNotIn("CNPJ:", corpo)
        self.assertTrue(corpo.endswith("Clínica"))


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
