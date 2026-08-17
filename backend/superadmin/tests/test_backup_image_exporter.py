"""Testes do exportador de imagens no backup."""
from django.test import SimpleTestCase

from superadmin.backup_service.image_exporter import (
    _looks_like_media_url,
    _split_url_list,
    pasta_pessoa,
)


class BackupImageExporterHelpersTest(SimpleTestCase):
    def test_media_server_url_reconhecida(self):
        url = "https://media.lwksistemas.com.br/files/12345678901/fotos/sample.jpg"
        self.assertTrue(_looks_like_media_url(url))

    def test_cloudinary_url_ainda_reconhecida(self):
        url = "https://res.cloudinary.com/demo/image/upload/v1/sample.jpg"
        self.assertTrue(_looks_like_media_url(url))

    def test_url_nao_media_rejeitada(self):
        self.assertFalse(_looks_like_media_url("https://example.com/page"))
        self.assertFalse(_looks_like_media_url(""))

    def test_split_url_list_json(self):
        raw = '["https://media.lwksistemas.com.br/files/a/fotos/x.jpg", "https://media.lwksistemas.com.br/files/a/fotos/y.png"]'
        urls = _split_url_list(raw)
        self.assertEqual(len(urls), 2)

    def test_split_url_list_texto(self):
        raw = "https://a.com/1.jpg, https://b.com/2.png"
        urls = _split_url_list(raw)
        self.assertEqual(urls, ["https://a.com/1.jpg", "https://b.com/2.png"])

    def test_pasta_pessoa_nome_e_cpf(self):
        self.assertEqual(
            pasta_pessoa(nome="LUIZ HENRIQUE FELIX", cpf="222.392.558-89"),
            "LUIZ_HENRIQUE_FELIX_22239255889",
        )

    def test_pasta_pessoa_so_nome(self):
        self.assertEqual(
            pasta_pessoa(nome="Renata Ribeiro Guariba", cpf=""),
            "Renata_Ribeiro_Guariba",
        )

    def test_pasta_pessoa_so_cpf(self):
        self.assertEqual(pasta_pessoa(nome="", cpf="349.992.498-41"), "34999249841")
