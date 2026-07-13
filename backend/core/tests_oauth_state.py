"""Testes do state OAuth assinado."""
from django.test import SimpleTestCase

from core.oauth_state import encode_oauth_state, parse_oauth_state


class OAuthStateTests(SimpleTestCase):
    def test_roundtrip_signed(self):
        state = encode_oauth_state(42, 7)
        loja_id, vendedor_id = parse_oauth_state(state)
        self.assertEqual(loja_id, 42)
        self.assertEqual(vendedor_id, 7)

    def test_legacy_format(self):
        loja_id, vendedor_id = parse_oauth_state("99:3")
        self.assertEqual(loja_id, 99)
        self.assertEqual(vendedor_id, 3)
