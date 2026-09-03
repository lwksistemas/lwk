"""Testes do exportador de imagens no backup."""
from django.test import SimpleTestCase

from superadmin.backup_service.image_exporter import (
    _looks_like_media_url,
    _prefixo_zip_url,
    _split_url_list,
    caminho_backup_midia,
    pasta_pessoa,
)


class BackupImageExporterHelpersTest(SimpleTestCase):
    def test_media_server_url_reconhecida(self):
        url = "https://media.lwksistemas.com.br/files/12345678901/fotos/sample.jpg"
        self.assertTrue(_looks_like_media_url(url))

    def test_cloudinary_e_outros_hosts_rejeitados(self):
        self.assertFalse(_looks_like_media_url("https://res.cloudinary.com/demo/image/upload/v1/sample.jpg"))
        self.assertFalse(_looks_like_media_url("https://example.com/page"))
        self.assertFalse(_looks_like_media_url("https://example.com/foto.jpg"))
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
            "luiz-henrique-felix_22239255889",
        )

    def test_pasta_pessoa_so_nome(self):
        self.assertEqual(
            pasta_pessoa(nome="Renata Ribeiro Guariba", cpf="", pessoa_id=2231),
            "renata-ribeiro-guariba_id2231",
        )

    def test_pasta_pessoa_so_cpf(self):
        self.assertEqual(pasta_pessoa(nome="", cpf="349.992.498-41"), "paciente_34999249841")

    def test_caminho_backup_segue_midia(self):
        self.assertEqual(
            caminho_backup_midia("luiz-henrique-felix_22239255889/fotos"),
            "luiz-henrique-felix_22239255889/fotos",
        )
        self.assertEqual(
            caminho_backup_midia("marcia-bataglia_id1825/docs"),
            "marcia-bataglia_id1825/pdf",
        )
        self.assertEqual(
            caminho_backup_midia("fotos/luiz-henrique-felix_22239255889"),
            "luiz-henrique-felix_22239255889/fotos",
        )
        self.assertEqual(caminho_backup_midia("admin/fotos"), "admin/fotos")
        self.assertEqual(caminho_backup_midia("fotos"), "admin/fotos")

    def test_prefixo_zip_usa_pasta_da_url(self):
        url = (
            "https://media.lwksistemas.com.br/files/37302743000126/"
            "luiz-henrique-felix_22239255889/pdf/termo.pdf"
        )
        self.assertEqual(
            _prefixo_zip_url(url),
            "imagens/luiz-henrique-felix_22239255889/pdf",
        )
