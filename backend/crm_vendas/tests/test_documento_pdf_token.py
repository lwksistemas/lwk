"""Testes de token público para download de PDF (proposta/contrato)."""
import time
from unittest.mock import patch

from django.test import SimpleTestCase

from crm_vendas.views_enviar_cliente import _criar_token, _verificar_token


class DocumentoPdfTokenTest(SimpleTestCase):
    def test_criar_e_verificar_token_valido(self):
        token = _criar_token('proposta', doc_id=42, loja_id=4)
        payload = _verificar_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['tipo'], 'proposta')
        self.assertEqual(payload['id'], 42)
        self.assertEqual(payload['loja_id'], 4)

    def test_token_expirado_rejeitado(self):
        with patch('crm_vendas.views_enviar_cliente.time') as mock_time:
            mock_time.time.return_value = 1_000_000
            token = _criar_token('contrato', doc_id=1, loja_id=2)
            mock_time.time.return_value = 1_000_000 + 4000
            self.assertIsNone(_verificar_token(token))

    def test_token_corrompido_rejeitado(self):
        self.assertIsNone(_verificar_token('token-invalido'))

    def test_token_contrato_preserva_tipo(self):
        token = _criar_token('contrato', doc_id=7, loja_id=3)
        payload = _verificar_token(token)
        self.assertEqual(payload['tipo'], 'contrato')
        self.assertGreater(payload['exp'], int(time.time()))
