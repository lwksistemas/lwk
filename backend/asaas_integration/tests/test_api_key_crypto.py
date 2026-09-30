"""A chave Asaas é um recurso só. Cada app grava a sua."""
from django.test import SimpleTestCase

from asaas_integration.api_key_utils import chave_asaas_em_claro, criptografar_asaas_api_key


class CriptografiaChaveAsaasTest(SimpleTestCase):
    def test_grava_cifrado_e_le_a_mesma_chave(self):
        chave = "$aact_prod_" + ("b" * 32)
        gravada = criptografar_asaas_api_key(chave)
        self.assertTrue(gravada.startswith("enc::"))
        self.assertEqual(chave_asaas_em_claro(gravada), chave)
        self.assertEqual(chave_asaas_em_claro(chave), chave)
