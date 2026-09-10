"""Status e datas da consulta só mudam pelos endpoints de ciclo de vida."""
from django.test import SimpleTestCase

from clinica_beleza.serializers.consultas import ConsultaSerializer


class ConsultaStatusReadOnlyTest(SimpleTestCase):
    def test_status_e_datas_sao_somente_leitura(self):
        for campo in ("status", "data_inicio", "data_fim"):
            self.assertIn(campo, ConsultaSerializer.Meta.read_only_fields)
