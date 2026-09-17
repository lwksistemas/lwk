"""Satisfação do cliente é obrigatória ao gravar evolução."""
from django.test import SimpleTestCase

from clinica_beleza.serializers.consultas import ConsultaEvolucaoSerializer


class EvolucaoSatisfacaoTests(SimpleTestCase):
    def test_vazio_pede_nota(self):
        s = ConsultaEvolucaoSerializer(data={"satisfacao": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("satisfacao", s.errors)
        self.assertIn("obrigatório", str(s.errors["satisfacao"][0]).lower())

    def test_nota_valida(self):
        s = ConsultaEvolucaoSerializer()
        self.assertEqual(s.fields["satisfacao"].to_internal_value(4), 4)
