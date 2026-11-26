"""Regressão: HTML da cobrança escapa clínica e corpo da mensagem."""
from django.test import SimpleTestCase

from clinica_beleza.cobranca_service import _montar_email_html_cobranca


class CobrancaEmailEscapeTest(SimpleTestCase):
    def test_escapa_clinica_e_markup_no_corpo(self):
        html_out = _montar_email_html_cobranca(
            'Olá <b>Ana</b>!\nClínica: <img src=x onerror=1>',
            {"clinica": '<script>x</script> Harmonis'},
        )
        self.assertNotIn("<script>", html_out)
        self.assertNotIn("<img", html_out)
        self.assertNotIn("<b>Ana</b>", html_out)
        self.assertIn("&lt;script&gt;", html_out)
        self.assertIn("&lt;b&gt;Ana&lt;/b&gt;", html_out)
        self.assertIn("<br>", html_out)
