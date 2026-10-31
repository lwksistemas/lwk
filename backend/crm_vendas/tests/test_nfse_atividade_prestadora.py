"""Atividade municipal padrão da empresa prestadora."""
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from crm_vendas.serializers.contas import ContaSerializer


class NfseAtividadePrestadoraTest(SimpleTestCase):
    def test_aceita_atividade_da_lista(self):
        self.assertEqual(
            ContaSerializer().validate_nfse_atividade_padrao("170601"),
            "170601",
        )

    def test_vazio_significa_padrao_da_loja(self):
        self.assertEqual(ContaSerializer().validate_nfse_atividade_padrao("  "), "")

    def test_recusa_codigo_fora_da_lista(self):
        with self.assertRaises(ValidationError):
            ContaSerializer().validate_nfse_atividade_padrao("999999")
