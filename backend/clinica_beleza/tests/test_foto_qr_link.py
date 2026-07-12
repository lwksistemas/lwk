"""Testes do link público de foto via QR."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.test import RequestFactory
from rest_framework import status

from clinica_beleza.foto_paciente_service import (
    ambiente_do_token_foto,
    build_link_foto,
    cloudinary_upload_config,
    default_frontend_base_foto,
    frontend_base_permitido,
    gerar_token_foto,
    resolver_frontend_base_qr,
)
from core.cloudinary_folders import resolve_ambiente_segment
from core.cloudinary_upload_preset import server_image_upload_options


class FotoQrLinkTests(TestCase):
    @patch('core.short_link.build_short_url', side_effect=lambda url, **_: url)
    def test_build_link_usa_query_token(self, _short):
        url = build_link_foto('abc:token', 'https://beta.lwksistemas.com.br')
        self.assertTrue(url.startswith('https://beta.lwksistemas.com.br/enviar-foto?t='))
        self.assertIn('abc%3Atoken', url)
        self.assertNotIn('/enviar-foto/abc:token', url)
        # Token Django nunca no path (lojas novas e existentes)
        path = url.split('?', 1)[0]
        self.assertNotIn('abc:token', path)

    def test_default_frontend_beta_por_ambiente(self):
        from django.test import override_settings

        with override_settings(LWK_ENVIRONMENT='staging'):
            self.assertEqual(default_frontend_base_foto(), 'https://beta.lwksistemas.com.br')
        with override_settings(LWK_ENVIRONMENT='production', FRONTEND_URL='https://lwksistemas.com.br'):
            self.assertEqual(default_frontend_base_foto(), 'https://lwksistemas.com.br')

    @patch('core.short_link.build_short_url')
    def test_build_link_encurta_para_qr(self, mock_short):
        mock_short.return_value = 'https://api.lwksistemas.com.br/r/abc12345'
        url = build_link_foto('abc:token', 'https://lwksistemas.com.br')
        self.assertEqual(url, 'https://api.lwksistemas.com.br/r/abc12345')
        full = mock_short.call_args[0][0]
        self.assertIn('/enviar-foto?t=abc%3Atoken', full)

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

    @patch('clinica_beleza.foto_paciente_service.build_link_foto')
    def test_gerar_qr_foto_usa_frontend_beta(self, mock_link):
        from types import SimpleNamespace
        from clinica_beleza.foto_paciente_service import gerar_qr_foto

        mock_link.return_value = 'https://beta.lwksistemas.com.br/enviar-foto?t=tok'
        consulta = SimpleNamespace(id=2, patient_id=1, loja_id=2)
        data = gerar_qr_foto(consulta, frontend_base='https://beta.lwksistemas.com.br')
        self.assertEqual(data['url'], 'https://beta.lwksistemas.com.br/enviar-foto?t=tok')
        mock_link.assert_called_once()
        self.assertEqual(mock_link.call_args[0][1], 'https://beta.lwksistemas.com.br')

    @patch('core.short_link.build_short_url', side_effect=lambda url, **kwargs: url)
    def test_fallback_settings_quando_sem_origin(self, _short):
        from django.test import override_settings

        with override_settings(FRONTEND_URL='https://lwksistemas.com.br'):
            url = build_link_foto('tok')
        self.assertTrue(url.startswith('https://lwksistemas.com.br/enviar-foto?t='))

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


class ConsultaFotoPermissaoStatusTests(TestCase):
    def _consulta(self, status_value):
        return SimpleNamespace(id=1, patient_id=2, loja_id=3, status=status_value)

    def test_geracao_qr_permitida_em_in_progress(self):
        from clinica_beleza.views_foto_paciente import _consulta_permite_envio_foto

        self.assertIsNone(_consulta_permite_envio_foto(self._consulta('IN_PROGRESS')))

    def test_geracao_qr_permitida_em_receber(self):
        from clinica_beleza.views_foto_paciente import _consulta_permite_envio_foto

        self.assertIsNone(_consulta_permite_envio_foto(self._consulta('RECEBER')))

    def test_geracao_qr_bloqueada_fora_de_atendimento(self):
        from clinica_beleza.views_foto_paciente import _consulta_permite_envio_foto

        res = _consulta_permite_envio_foto(self._consulta('SCHEDULED'))
        self.assertIsNotNone(res)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
