"""Tipos de agenda padrão: Consulta e Retorno."""
from django.test import SimpleTestCase

from clinica_beleza.procedimentos_catalogo import (
    is_tipo_agenda_sistema,
    nomes_agenda_faltando,
)


class NomesAgendaPadraoTests(SimpleTestCase):
    def test_nao_duplica_consulta_em_caixa_diferente(self):
        self.assertEqual(nomes_agenda_faltando(["CONSULTA"]), ["Retorno"])

    def test_loja_nova_recebe_consulta_e_retorno(self):
        self.assertEqual(nomes_agenda_faltando([]), ["Consulta", "Retorno"])

    def test_sistema_reconhece_consulta_e_retorno(self):
        self.assertTrue(is_tipo_agenda_sistema("consulta"))
        self.assertTrue(is_tipo_agenda_sistema("RETORNO"))
        self.assertFalse(is_tipo_agenda_sistema("Estética"))
