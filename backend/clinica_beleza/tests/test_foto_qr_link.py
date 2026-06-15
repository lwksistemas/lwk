"""Testes do link público de foto via QR."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from clinica_beleza.foto_paciente_service import (
    ambiente_do_token_foto,
    build_link_foto,
    cloudinary_upload_config,
    frontend_base_permitido,
    gerar_token_foto,
    resolver_frontend_base_qr,
)
from core.cloudinary_folders import resolve_ambiente_segment
from core.cloudinary_upload_preset import server_image_upload_options


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

    def test_resolve_ambiente_beta(self):
        self.assertEqual(
            resolve_ambiente_segment('https://beta.lwksistemas.com.br'),
            'beta',
        )

    def test_token_qr_grava_ambiente_beta(self):
        token = gerar_token_foto(1, 2, 3, ambiente='beta')
        from clinica_beleza.foto_paciente_service import decodificar_token_foto

        payload = decodificar_token_foto(token)
        self.assertEqual(payload['ambiente'], 'beta')

    def test_ambiente_do_token_fallback_request(self):
        req = SimpleNamespace(
            headers={'Origin': 'https://beta.lwksistemas.com.br'},
            META={},
        )
        self.assertEqual(ambiente_do_token_foto({}, req), 'beta')

    def test_server_upload_usa_asset_folder(self):
        opts = server_image_upload_options('lwksistemas/beta/34787081845/clinica-beleza-fotos')
        self.assertEqual(opts['asset_folder'], 'lwksistemas/beta/34787081845/clinica-beleza-fotos')
        self.assertTrue(opts['use_asset_folder_as_public_id_prefix'])

    def test_cloudinary_upload_config_com_ambiente(self):
        loja = SimpleNamespace(
            cpf_cnpj='34787081845',
            slug='34787081845',
            atalho='sorriso',
            id=2,
        )
        cfg = cloudinary_upload_config(loja, ambiente='beta')
        self.assertEqual(
            cfg['folder'],
            'lwksistemas/beta/34787081845/clinica-beleza-fotos',
        )
