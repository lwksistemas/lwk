"""Logo principal da clínica na marca d'água das assinaturas do termo."""
from types import SimpleNamespace
from unittest import TestCase

from clinica_beleza.termo_consentimento_pdf import (
    WM_OPACIDADE,
    _logo_url_loja,
)


class LogoUrlLojaTermoTest(TestCase):
    def test_usa_logo_principal(self):
        loja = SimpleNamespace(
            logo="https://media.example/logo.png",
            login_logo="https://media.example/login.png",
        )
        self.assertEqual(_logo_url_loja(loja), "https://media.example/logo.png")

    def test_fallback_logo_login(self):
        loja = SimpleNamespace(logo="", login_logo="https://media.example/login.png")
        self.assertEqual(_logo_url_loja(loja), "https://media.example/login.png")

    def test_sem_loja(self):
        self.assertEqual(_logo_url_loja(None), "")

    def test_marca_dagua_mais_visivel_que_crm(self):
        self.assertGreater(WM_OPACIDADE, 0.25)
        self.assertLessEqual(WM_OPACIDADE, 0.9)
