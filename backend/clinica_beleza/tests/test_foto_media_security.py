"""Testes de validação de URL de mídia e token QR de fotos."""
from types import SimpleNamespace
from unittest import TestCase

from clinica_beleza.foto_paciente_service.exceptions import FotoUrlInvalida
from clinica_beleza.foto_paciente_service.token_qr import (
    decodificar_token_foto,
    gerar_token_foto,
)
from clinica_beleza.foto_paciente_service.validation import validar_foto_loja
from core.media_storage import is_media_url, parse_media_url


class MediaUrlSecurityTests(TestCase):
    def test_is_media_url_rejeita_host_sufixo(self):
        evil = "https://media.lwksistemas.com.br.evil.com/files/41449198000172/fotos/a.jpg"
        self.assertFalse(is_media_url(evil))

    def test_is_media_url_rejeita_path_com_prefixo(self):
        evil = "https://media.lwksistemas.com.br/evil/files/41449198000172/fotos/a.jpg"
        self.assertFalse(is_media_url(evil))
        self.assertIsNone(parse_media_url(evil))

    def test_is_media_url_aceita_url_legitima(self):
        url = "https://media.lwksistemas.com.br/files/41449198000172/fotos/abc123.jpg"
        self.assertTrue(is_media_url(url))
        self.assertEqual(
            parse_media_url(url),
            ("41449198000172", "fotos", "abc123.jpg"),
        )

    def test_is_media_url_aceita_pasta_paciente(self):
        url = "https://media.lwksistemas.com.br/files/41449198000172/fotos/maria-silva_12345678901/abc.jpg"
        self.assertTrue(is_media_url(url))
        self.assertEqual(
            parse_media_url(url),
            ("41449198000172", "fotos/maria-silva_12345678901", "abc.jpg"),
        )

    def test_validar_foto_loja_rejeita_outro_cnpj(self):
        loja = SimpleNamespace(cpf_cnpj="41449198000172", cnpj="41449198000172")
        url = "https://media.lwksistemas.com.br/files/00000000000000/fotos/a.jpg"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(loja, url)

    def test_validar_foto_loja_rejeita_pasta_docs(self):
        loja = SimpleNamespace(cpf_cnpj="41449198000172", cnpj="41449198000172")
        url = "https://media.lwksistemas.com.br/files/41449198000172/docs/a.pdf"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(loja, url)

    def test_validar_foto_loja_aceita_fotos_da_loja(self):
        loja = SimpleNamespace(cpf_cnpj="41449198000172", cnpj="41449198000172")
        url = "https://media.lwksistemas.com.br/files/41449198000172/fotos/abc.jpg"
        validar_foto_loja(loja, url)  # não levanta

    def test_validar_foto_loja_aceita_fotos_paciente(self):
        loja = SimpleNamespace(cpf_cnpj="41449198000172", cnpj="41449198000172")
        url = "https://media.lwksistemas.com.br/files/41449198000172/fotos/joao_12345678901/abc.jpg"
        validar_foto_loja(loja, url)


class TokenFotoSecurityTests(TestCase):
    def test_token_exige_modulo(self):
        token = gerar_token_foto(1, 2, 3, ambiente="producao")
        payload = decodificar_token_foto(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["modulo"], "clinica_beleza")
        self.assertEqual(payload["consulta_id"], 1)
