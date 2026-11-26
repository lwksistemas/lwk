"""Regressão: campos livres do termo não podem injetar markup no PDF."""
from django.test import SimpleTestCase

from clinica_beleza.termo_consentimento_pdf import _pdf_multiline, _pdf_text


class TermoPdfEscapeTest(SimpleTestCase):
    def test_escape_tags_e_ampersand(self):
        raw = '<script>alert(1)</script> & "x"'
        out = _pdf_text(raw)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("&amp;", out)

    def test_multiline_preserva_br_apos_escape(self):
        out = _pdf_multiline("a <b>x</b>\nlinha2")
        self.assertIn("<br/>", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>x</b>", out)
