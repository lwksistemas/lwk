"""Regras de NFS-e da loja, sem chamar prefeitura nem Asaas."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.issnet_nacional_client import ISSNetNacionalClient
from nfse_integration.issnet_nacional_xml_builder import (
    _motivo_cancelamento_nacional,
    construir_xml_cancelar_nfse_nacional,
    construir_xml_consultar_url_nfse_nacional,
)
from nfse_integration.loja_nfse_api import (
    ConfigLojaInconsistenteError,
    ExclusaoNFSeLojaError,
    _consultar_nfse_issnet_por_rps,
    _sincronizar_nfse_issnet_nacional,
    _copiar_campos_numericos_portal,
    _copiar_campos_portal,
    _sanitizar_resultado_recuperacao,
    _series_rps_candidatas,
    processar_emissao_nfse_loja,
    provedor_nf_loja,
    sincronizar_nfse_asaas_loja,
    validar_config_crm_loja,
    validar_exclusao_nfse_loja,
    xml_nfse_conteudo,
)


class LojaNfseRegrasTests(SimpleTestCase):
    def test_config_de_outra_loja_e_recusada(self):
        with self.assertRaises(ConfigLojaInconsistenteError):
            validar_config_crm_loja(SimpleNamespace(id=1), SimpleNamespace(loja_id=2))
        validar_config_crm_loja(SimpleNamespace(id=4), SimpleNamespace(loja_id=4))

    def test_provedor_padrao_e_asaas(self):
        self.assertEqual(provedor_nf_loja(SimpleNamespace()), "issnet")
        self.assertEqual(provedor_nf_loja(SimpleNamespace(provedor_nf=" Asaas ")), "asaas")

    def test_nota_emitida_ou_cancelada_nao_exclui(self):
        with self.assertRaises(ExclusaoNFSeLojaError) as emitida:
            validar_exclusao_nfse_loja(SimpleNamespace(status="emitida"))
        self.assertIn("Cancelar", emitida.exception.message)
        with self.assertRaises(ExclusaoNFSeLojaError):
            validar_exclusao_nfse_loja(SimpleNamespace(status="cancelada"))
        validar_exclusao_nfse_loja(SimpleNamespace(status="rascunho"))

    def test_xml_prefere_a_nota_e_cai_no_rps(self):
        self.assertEqual(xml_nfse_conteudo(SimpleNamespace(xml_nfse="<nf/>", xml_rps="<rps/>")), "<nf/>")
        self.assertEqual(xml_nfse_conteudo(SimpleNamespace(xml_nfse="", xml_rps="<rps/>")), "<rps/>")

    def test_series_rps_inclui_alternativas(self):
        self.assertEqual(_series_rps_candidatas(SimpleNamespace(issnet_serie_rps="E")), ["E", "1", "NF"])
        self.assertEqual(_series_rps_candidatas(SimpleNamespace(issnet_serie_rps="")), ["1", "E", "NF"])

    def test_tomador_igual_ao_prestador_sai_do_resultado(self):
        out = _sanitizar_resultado_recuperacao(
            {"tomador_cpf_cnpj": "12.345.678/0001-90", "numero_nf": "9"},
            "12345678000190",
        )
        self.assertEqual(out["tomador_cpf_cnpj"], "")
        self.assertEqual(out["numero_nf"], "9")

    def test_portal_nao_copia_cnpj_do_proprio_prestador(self):
        out = {}
        _copiar_campos_portal(
            out,
            {"tomador_nome": "Ana", "tomador_cpf_cnpj": "12345678000190"},
            "12345678000190",
            False,
        )
        self.assertEqual(out, {"tomador_nome": "Ana"})
        _copiar_campos_numericos_portal(out, {"valor": "10.50"}, False)
        self.assertEqual(out["valor"], 10.5)

    def test_emissao_enfileira_sem_chamar_o_provedor(self):
        with (
            patch("nfse_integration.queue_dispatch.should_enqueue_nfse", return_value=True),
            patch("nfse_integration.queue_dispatch.enqueue_emissao_nfse_loja") as enfileirar,
        ):
            body, code = processar_emissao_nfse_loja(SimpleNamespace(id=1), 4, {"servico_descricao": "Consulta"})
        self.assertEqual(code, 202)
        self.assertTrue(body["queued"])
        enfileirar.assert_called_once_with(4, {"servico_descricao": "Consulta"})

    def test_sync_asaas_recusa_nota_de_outro_provedor_e_loja_sem_chave(self):
        body, code = sincronizar_nfse_asaas_loja(SimpleNamespace(provedor="issnet"), 4)
        self.assertEqual(code, 400)
        self.assertIn("Asaas", body["error"])

        with patch(
            "nfse_integration.loja_nfse_api._resolver_config_nfse_loja",
            return_value=SimpleNamespace(asaas_api_key=""),
        ):
            body, code = sincronizar_nfse_asaas_loja(SimpleNamespace(provedor="asaas"), 4)
        self.assertEqual(code, 400)
        self.assertIn("API Key", body["error"])

    def test_consulta_por_rps_para_em_nota_cancelada(self):
        client = MagicMock()
        client.consultar_nfse_por_rps.return_value = {"cancelada": True}

        class _Cliente:
            def __enter__(self):
                return client

            def __exit__(self, *args):
                return False

        with patch("nfse_integration.issnet_loja.issnet_client_loja", return_value=_Cliente()):
            parsed, err = _consultar_nfse_issnet_por_rps(
                SimpleNamespace(issnet_serie_rps="1", inscricao_municipal="1"),
                SimpleNamespace(cpf_cnpj="123", inscricao_municipal=""),
                10,
                serie_rps="1",
            )
        self.assertIsNone(parsed)
        self.assertIn("cancelada", err)

    def test_xml_de_cancelamento_e_o_evento_nacional(self):
        chave = "1" * 50
        xml = construir_xml_cancelar_nfse_nacional(
            numero_nfse="123",
            prestador_cnpj="12.345.678/0001-90",
            prestador_inscricao_municipal="999",
            codigo_cancelamento="1",
            chave_acesso=chave,
            motivo_cancelamento="Erro na emissão",
            dh_evento=datetime(2026, 10, 12, 15, 0, tzinfo=timezone(timedelta(hours=-3))),
        )
        self.assertIn("pedRegEvento", xml)
        self.assertIn(f"PRE{chave}101103", xml)
        self.assertIn("12345678000190", xml)
        self.assertNotIn("nPedRegEvento", xml)
        self.assertIn("e101103", xml)
        self.assertLess(xml.index("<chNFSe>"), xml.index("<e101103>"))
        self.assertIn("2026-10-12T15:00:00-03:00", xml)
        self.assertNotIn("CPFAutor", xml)
        self.assertNotIn("InfPedidoCancelamento", xml)
        codigo, texto = _motivo_cancelamento_nacional("1", "Teste sistema")
        self.assertEqual(codigo, "1")
        self.assertGreaterEqual(len(texto), 15)
        self.assertIn("Teste sistema", texto)

    def test_xml_da_url_usa_cnpj_im_e_pagina(self):
        xml = construir_xml_consultar_url_nfse_nacional(
            numero_nf="181",
            prestador_cnpj="12.345.678/0001-90",
            prestador_inscricao_municipal="88.776",
        )
        self.assertIn("<CNPJ>12345678000190</CNPJ>", xml)
        self.assertIn("<IM>88776</IM>", xml)
        self.assertIn("<NumeroNfse>181</NumeroNfse>", xml)
        self.assertIn("<Pagina>1</Pagina>", xml)
        self.assertNotIn("Pedido", xml)
        self.assertNotIn("CpfCnpj", xml)

    def test_le_a_url_nacional_da_resposta(self):
        url = ISSNetNacionalClient._extrair_url_danfe_resposta(
            "<UrlVisualizacaoNfseNacional>https://exemplo/danfe</UrlVisualizacaoNfseNacional>"
        )
        self.assertEqual(url, "https://exemplo/danfe")

    def test_prefere_a_url_nacional_mesmo_escapada_no_soap(self):
        soap = (
            "<soap:Body><outputXML>"
            "&lt;ConsultarUrlNfseResposta xmlns=&quot;http://www.sped.fazenda.gov.br/nfse&quot;&gt;"
            "&lt;ListaLinks&gt;&lt;Links&gt;"
            "&lt;IdentificacaoNfse&gt;&lt;nDFSe&gt;181&lt;/nDFSe&gt;&lt;/IdentificacaoNfse&gt;"
            "&lt;UrlVisualizacaoNfse&gt;https://www.notaeletronica.com.br/municipal&lt;/UrlVisualizacaoNfse&gt;"
            "&lt;UrlVisualizacaoNfseNacional&gt;https://www.nfse.gov.br/consulta?chave=ABC&lt;/UrlVisualizacaoNfseNacional&gt;"
            "&lt;/Links&gt;&lt;/ListaLinks&gt;"
            "&lt;/ConsultarUrlNfseResposta&gt;"
            "</outputXML></soap:Body>"
        )
        url = ISSNetNacionalClient._extrair_url_danfe_resposta(soap)
        self.assertEqual(url, "https://www.nfse.gov.br/consulta?chave=ABC")

    def test_sincronizar_nacional_nao_consulta_a_prefeitura(self):
        nfse = SimpleNamespace(status="cancelada", save=MagicMock(), refresh_from_db=MagicMock())
        with patch(
            "nfse_integration.issnet_nacional_client.ISSNetNacionalClient.consultar_nfse_por_dps",
            side_effect=AssertionError("não deve consultar a prefeitura"),
        ):
            body, code = _sincronizar_nfse_issnet_nacional(
                nfse=nfse,
                loja=SimpleNamespace(),
                loja_id=4,
                config=SimpleNamespace(),
                numero_rps=187,
                serie_rps="1",
                cnpj_prestador="1",
                im_prestador="2",
            )
        self.assertEqual(code, 200)
        self.assertTrue(body["aviso"])
        self.assertIn("link oficial", body["message"])
        self.assertIn("continua cancelada", body["message"])
        self.assertEqual(nfse.status, "cancelada")
        nfse.save.assert_not_called()
        nfse.refresh_from_db.assert_not_called()
