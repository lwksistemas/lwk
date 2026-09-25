"""Filtro da lista de clientes."""
from django.test import SimpleTestCase

from clinica_beleza.views_pacientes import situacao_lista_pacientes


class SituacaoListaPacientesTest(SimpleTestCase):
    def test_padrao_da_api_sem_parametro_continua_ativos(self):
        self.assertEqual(situacao_lista_pacientes(None), "ativos")

    def test_com_consulta_finalizada(self):
        self.assertEqual(situacao_lista_pacientes("com_consulta"), "com_consulta")

    def test_active_false_lista_todos(self):
        self.assertEqual(situacao_lista_pacientes(None, "false"), "todos")

    def test_situacao_desconhecida_cai_em_ativos(self):
        self.assertEqual(situacao_lista_pacientes("qualquer"), "ativos")
