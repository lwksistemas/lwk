"""Testes do link público de foto via QR."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from clinica_beleza.foto_paciente_service import (
    build_link_foto,
    frontend_base_permitido,
    resolver_frontend_base_qr,
)


class FotoQrLinkTests(TestCase):
    def test_build_link_usa_base_beta(self):
        url = build_link_foto('abc:token', 'https://beta.lwksistemas.com.br')
        self.assertTrue(url.startswith('https://beta.lwksistemas.com.br/enviar-foto/'))

    def test_frontend_base_permitido_beta(self):
        self.assertEqual(
            frontend_base_permitido('https://beta.lwksistemas.com.br'),
            'https://beta.lwksistemas.com.br',
        )

    def test_frontend_base_rejeita_dominio_externo(self):
        self.assertIsNone(frontend_base_permitido('https://evil.example.com'))

    def test_resolver_usa_origin_do_request(self):
        req = SimpleNamespace(
            data={},
            headers={'Origin': 'https://beta.lwksistemas.com.br'},
            META={},
        )
        self.assertEqual(
            resolver_frontend_base_qr(req),
            'https://beta.lwksistemas.com.br',
        )

    def test_resolver_usa_frontend_origin_no_body(self):
        req = SimpleNamespace(data={}, headers={}, META={})
        base = resolver_frontend_base_qr(
            req,
            'https://beta.lwksistemas.com.br',
        )
        self.assertEqual(base, 'https://beta.lwksistemas.com.br')

    @patch('clinica_beleza.foto_paciente_service.getattr')
    def test_fallback_settings_quando_sem_origin(self, mock_getattr):
        mock_getattr.return_value = 'https://lwksistemas.com.br'
        url = build_link_foto('tok')
        self.assertTrue(url.startswith('https://lwksistemas.com.br/enviar-foto/'))
