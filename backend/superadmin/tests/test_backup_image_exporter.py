"""Testes do exportador de imagens no backup."""
from django.test import SimpleTestCase

from superadmin.backup_service.image_exporter import (
    _looks_like_media_url,
    _split_url_list,
)


class BackupImageExporterHelpersTest(SimpleTestCase):
    def test_cloudinary_url_reconhecida(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v1/sample.jpg'
        self.assertTrue(_looks_like_media_url(url))

    def test_url_nao_media_rejeitada(self):
        self.assertFalse(_looks_like_media_url('https://example.com/page'))
        self.assertFalse(_looks_like_media_url(''))

    def test_split_url_list_json(self):
        raw = '["https://res.cloudinary.com/a/x.jpg", "https://res.cloudinary.com/a/y.png"]'
        urls = _split_url_list(raw)
        self.assertEqual(len(urls), 2)

    def test_split_url_list_texto(self):
        raw = 'https://a.com/1.jpg, https://b.com/2.png'
        urls = _split_url_list(raw)
        self.assertEqual(urls, ['https://a.com/1.jpg', 'https://b.com/2.png'])
