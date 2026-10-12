"""URL da DANFE, XML reconstruído e campos gravados na recuperação. Sem prefeitura."""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.asaas_webhook_sync import (
    _mensagem_erro_invoice_asaas,
    aplicar_objeto_invoice_asaas_em_nfse,
)
from nfse_integration.danfe import url_danfe_valida, url_xml_download_from_danfe
from nfse_integration.issnet_shared import normalizar_codigo_cancelamento
from nfse_integration.issnet_soap import (
    cdata_section,
    issnet_corpo_parece_xml,
    issnet_decodificar_corpo,
    issnet_erro_assinatura,
    issnet_erro_schema_ou_cabecalho,
    issnet_fault_soap_generico,
    strip_xml_declaration,
)
from nfse_integration.persistencia_nfse_loja import (
    _aplicar_campo_tomador_cpf_cnpj,
    _aplicar_campos_scalares_nfse,
    gerar_proximo_numero_rps,
    nfse_importacao_incompleta,
)
from nfse_integration.queue_serialize import deserialize_validated_data, serialize_validated_data
from nfse_integration.xml_nfse_loja import gerar_xml_nfse_reconstruido, nfse_precisa_buscar_xml


class DanfeEXmlTests(SimpleTestCase):
    def test_url_de_schema_nao_e_danfe(self):
        self.assertFalse(url_danfe_valida("http://www.w3.org/2001/XMLSchema"))
        self.assertTrue(url_danfe_valida("https://nfse.issnetonline.com.br/nota"))
        self.assertEqual(
            url_xml_download_from_danfe("https://exemplo/Nota_Digital_Nacional.aspx?id=1"),
            "https://exemplo/NotaDigitalXmlDownload.aspx?id=1",
        )
        self.assertEqual(url_xml_download_from_danfe(""), "")

    def test_reconstrui_cnpj_do_tomador_e_sabe_quando_falta_xml(self):
        loja = SimpleNamespace(nome="Felix & Cia", cpf_cnpj="12.345.678/0001-90", inscricao_municipal="99")
        nfse = SimpleNamespace(
            numero_nf="55",
            codigo_verificacao="ABC",
            data_emissao=datetime(2026, 10, 12, 10, 0),
            numero_rps=12,
            valor=Decimal("150"),
            valor_iss=Decimal("3"),
            aliquota_iss=Decimal("2"),
            servico_descricao="A & B",
            tomador_cpf_cnpj="12345678000190",
            tomador_nome="Ana",
            xml_nfse="",
            xml_rps="",
            provedor="issnet",
            status="emitida",
        )
        xml = gerar_xml_nfse_reconstruido(nfse, loja)
        self.assertIn("<Cnpj>12345678000190</Cnpj>", xml)
        self.assertIn("Felix &amp; Cia", xml)
        self.assertTrue(nfse_precisa_buscar_xml(nfse))
        nfse.xml_nfse = "<nf/>"
        self.assertFalse(nfse_precisa_buscar_xml(nfse))

    def test_importacao_so_com_numero_esta_incompleta(self):
        nfse = SimpleNamespace(valor=0, tomador_nome="", tomador_cpf_cnpj="", xml_nfse="", xml_rps="", provedor="issnet", status="emitida")
        self.assertTrue(nfse_importacao_incompleta(nfse))
        self.assertFalse(nfse_importacao_incompleta(None))


class PersistenciaEFilaTests(SimpleTestCase):
    def test_documento_do_prestador_nao_fica_como_tomador(self):
        nfse = SimpleNamespace(tomador_cpf_cnpj="111")
        loja = SimpleNamespace(cpf_cnpj="999")
        campos = _aplicar_campo_tomador_cpf_cnpj(nfse, {"tomador_cpf_cnpj": "999"}, loja)
        self.assertEqual(campos, ["tomador_cpf_cnpj"])
        self.assertEqual(nfse.tomador_cpf_cnpj, "")

        outro = SimpleNamespace(tomador_cpf_cnpj="")
        _aplicar_campo_tomador_cpf_cnpj(outro, {"tomador_cpf_cnpj": "39053344705"}, loja)
        self.assertIn("390.533.447-05", outro.tomador_cpf_cnpj)

    def test_aplica_valor_e_descricao(self):
        nfse = SimpleNamespace()
        campos = _aplicar_campos_scalares_nfse(
            nfse,
            {"servico_descricao": "Consulta", "valor": "150.00", "aliquota_iss": "2"},
        )
        self.assertIn("servico_descricao", campos)
        self.assertIn("valor", campos)
        self.assertEqual(nfse.valor, "150.00")

    @patch("nfse_integration.models.NFSe")
    def test_proximo_rps_passa_do_maior_e_do_portal(self, nfse_model):
        nfse_model.objects.filter.return_value.aggregate.return_value = {"m": 8}
        config = SimpleNamespace(nacional_ultimo_dps=10, issnet_ultimo_rps_conhecido=0)
        self.assertEqual(gerar_proximo_numero_rps(4, config), 11)

    def test_fila_guarda_decimal_e_data_como_texto(self):
        dia = datetime(2026, 10, 12)
        out = serialize_validated_data({"valor_servicos": Decimal("10.50"), "data": dia, "nome": "Ana"})
        self.assertEqual(out["valor_servicos"], "10.50")
        self.assertEqual(out["data"], dia.isoformat())
        volta = deserialize_validated_data(out)
        self.assertEqual(volta["valor_servicos"], Decimal("10.50"))


class AsaasInvoiceESoapTests(SimpleTestCase):
    def test_codigo_de_cancelamento_desconhecido_cai_em_erro_na_emissao(self):
        self.assertEqual(normalizar_codigo_cancelamento("4"), "4")
        self.assertEqual(normalizar_codigo_cancelamento("9"), "1")
        self.assertEqual(normalizar_codigo_cancelamento(None), "1")

    def test_invoice_com_erro_marca_a_nota(self):
        nfse = MagicMock()
        nfse.id = 7
        ok = aplicar_objeto_invoice_asaas_em_nfse(
            nfse,
            {"status": "ERROR", "message": "Rejeitada pela prefeitura"},
            "INVOICE_ERROR",
        )
        self.assertTrue(ok)
        self.assertEqual(nfse.status, "erro")
        self.assertIn("prefeitura", nfse.erro)
        nfse.save.assert_called_once()
        self.assertIn("code", _mensagem_erro_invoice_asaas({"errors": [{"code": "x"}]}))
        self.assertEqual(_mensagem_erro_invoice_asaas({}), "Erro na emissão (Asaas).")

    def test_invoice_autorizada_limpa_o_erro_e_guarda_o_pdf(self):
        nfse = MagicMock()
        nfse.id = 7
        nfse.erro = "antigo"
        nfse.pdf_url = ""
        ok = aplicar_objeto_invoice_asaas_em_nfse(
            nfse,
            {"status": "AUTHORIZED", "pdfUrl": "https://exemplo/nota.pdf"},
        )
        self.assertTrue(ok)
        self.assertEqual(nfse.status, "emitida")
        self.assertEqual(nfse.erro, "")
        self.assertEqual(nfse.pdf_url, "https://exemplo/nota.pdf")

    def test_soap_reconhece_fault_schema_e_assinatura(self):
        self.assertTrue(strip_xml_declaration('<?xml version="1.0"?><a/>').startswith("<a"))
        self.assertIn("]]]]><![CDATA[>", cdata_section("a]]>b"))
        self.assertTrue(issnet_corpo_parece_xml("  <ok/>"))
        self.assertFalse(issnet_corpo_parece_xml("texto"))
        fault = "<faultcode>s:Client</faultcode><faultstring>Error</faultstring>"
        self.assertTrue(issnet_fault_soap_generico(fault))
        self.assertTrue(issnet_erro_schema_ou_cabecalho("XML schema inválido"))
        self.assertTrue(issnet_erro_assinatura("E0714 erro na assinatura"))
        self.assertFalse(issnet_erro_assinatura("<ListaNfse><Mensagem>erro na assinatura</Mensagem></ListaNfse>"))
        resposta = SimpleNamespace(content="Olá".encode("utf-8"), text="")
        self.assertEqual(issnet_decodificar_corpo(resposta), "Olá")
