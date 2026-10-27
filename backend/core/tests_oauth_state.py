"""Testes do state OAuth assinado."""
from django.test import SimpleTestCase

from core.oauth_state import encode_oauth_state, parse_oauth_state


class OAuthStateTests(SimpleTestCase):
    def test_roundtrip_signed(self):
        state = encode_oauth_state(42, 7)
        loja_id, vendedor_id = parse_oauth_state(state)
        self.assertEqual(loja_id, 42)
        self.assertEqual(vendedor_id, 7)

    def test_numero_da_loja_sem_assinatura_nao_vale(self):
        self.assertEqual(parse_oauth_state("99"), (None, None))
        self.assertEqual(parse_oauth_state("99:3"), (None, None))
