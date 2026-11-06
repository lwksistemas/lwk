"""A nota da loja na API Nacional sai em produção e com o código da Sefin."""
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from nfse_integration.emissao_issnet_nacional_loja import codigo_tributacao_nacional_sefin
from nfse_integration.emissao_nacional_loja import (
    _montar_resultado_emissao_nacional,
    ambiente_nacional_loja,
)


class AmbienteNacionalLojaTests(SimpleTestCase):
    def test_crm_sem_campo_de_ambiente_emite_em_producao(self):
        config = SimpleNamespace(issnet_ambiente_homologacao=False)
        self.assertEqual(ambiente_nacional_loja(config), "producao")

    def test_homologacao_explicita_permanece(self):
        config = SimpleNamespace(nacional_ambiente="homologacao", issnet_ambiente_homologacao=False)
        self.assertEqual(ambiente_nacional_loja(config), "homologacao")

    def test_codigo_municipal_1706_vai_para_a_lista_nacional(self):
        config = SimpleNamespace(
            codigo_servico_municipal="1706.01",
            codigo_tributacao_nacional="170601",
            item_lista_servico="1706",
            aliquota_iss=Decimal("2.50"),
            optante_simples_nacional=True,
            p_tot_trib_sn=None,
        )
        self.assertEqual(codigo_tributacao_nacional_sefin(config, "1706.01"), "170601")

    def test_grava_o_numero_curto_e_a_chave_na_verificacao(self):
        chave = "1" * 50
        xml = "<NFSe xmlns='http://www.sped.fazenda.gov.br/nfse'><infNFSe><nNFSe>000000000000001</nNFSe></infNFSe></NFSe>"
        resultado = _montar_resultado_emissao_nacional(
            {"chave_acesso": chave, "xml_nfse": xml, "nsu_recepcao": "DPS123"},
            191, Decimal("6.00"), Decimal("2.50"), Decimal("0.15"),
            "LWK", "24758458000172", "TESTE",
        )
        self.assertEqual(resultado["numero_nf"], "1")
        self.assertEqual(resultado["codigo_verificacao"], chave)
        self.assertIn("<nNFSe>", resultado["xml_nfse"])
