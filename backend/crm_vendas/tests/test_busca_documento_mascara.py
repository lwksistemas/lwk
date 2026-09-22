"""Busca de CNPJ/CPF ignora a máscara gravada no cadastro."""
import re

from django.test import SimpleTestCase

from crm_vendas.views_common import q_contem_digitos_ignorando_mascara


class BuscaDocumentoMascaraTests(SimpleTestCase):
    def test_cnpj_so_digitos_encontra_valor_formatado(self):
        consulta = q_contem_digitos_ignorando_mascara("cnpj", "52834101000161")
        padrao = consulta.children[0][1]
        self.assertRegex("52.834.101/0001-61", padrao)

    def test_termo_curto_nao_gera_filtro(self):
        consulta = q_contem_digitos_ignorando_mascara("cnpj", "52")
        self.assertEqual(consulta.children, [])

    def test_padrao_casa_telefone_com_mascara(self):
        consulta = q_contem_digitos_ignorando_mascara("telefone", "11988887777")
        padrao = consulta.children[0][1]
        self.assertIsNotNone(re.search(padrao, "(11) 98888-7777"))
