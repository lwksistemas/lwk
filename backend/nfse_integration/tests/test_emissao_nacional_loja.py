"""A nota da loja na API Nacional sai em produção e com o código da Sefin."""
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from nfse_integration.emissao_issnet_nacional_loja import codigo_tributacao_nacional_sefin
from nfse_integration.emissao_nacional_loja import ambiente_nacional_loja


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
