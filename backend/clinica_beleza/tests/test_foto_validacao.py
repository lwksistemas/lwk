"""Testes de segurança para validação de URLs de fotos de pacientes."""
from django.contrib.auth.models import User
from django.test import TestCase

from superadmin.models import Loja, PlanoAssinatura, TipoLoja

from ..foto_paciente_service.exceptions import FotoUrlInvalida
from ..foto_paciente_service.validation import validar_foto_loja


class FotoUrlValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner_test",
            email="owner@test.com",
            password="pass",
        )
        self.tipo = TipoLoja.objects.create(
            nome="Clínica da Beleza",
            descricao="",
            slug="clinica-beleza",
        )
        self.plano = PlanoAssinatura.objects.create(
            nome="Básico",
            slug="basico",
            descricao="",
            preco_mensal=99,
            preco_anual=990,
        )
        self.plano.tipos_loja.add(self.tipo)
        self.loja = Loja.objects.create(
            nome="Clínica Test",
            slug="41449198000172",
            atalho="clinicatest",
            owner=self.user,
            tipo_loja=self.tipo,
            plano=self.plano,
            cpf_cnpj="41449198000172",
            is_active=True,
        )

    def test_rejeita_url_cloudinary(self):
        url = "https://res.cloudinary.com/exemplo/image/upload/v123/foto.jpg"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(self.loja, url)

    def test_rejeita_url_cloudinary_com(self):
        url = "https://cloudinary.com/exemplo/foto.jpg"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(self.loja, url)

    def test_rejeita_url_nao_https(self):
        url = "http://lwksistemas.com.br/files/41449198000172/fotos/foto.jpg"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(self.loja, url)

    def test_rejeita_url_outro_dominio(self):
        url = "https://outro-site.com/files/41449198000172/fotos/foto.jpg"
        with self.assertRaises(FotoUrlInvalida):
            validar_foto_loja(self.loja, url)
