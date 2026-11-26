"""Regressão: campos livres do termo não podem injetar markup no PDF."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from clinica_beleza.termo_consentimento_pdf import (
    _build_conteudo_texto_termo,
    _criar_styles_termo,
    _pdf_multiline,
    _pdf_text,
)


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

    def test_build_conteudo_escapa_payload_em_paragraph(self):
        """Garante que o fluxo real do PDF escapa; não só os helpers unitários."""
        styles = getSampleStyleSheet()
        _, _, body_style, _ = _criar_styles_termo(styles)
        elements = []
        payload = "<b>aberto</b> <img src='http://127.0.0.1:1/x.png'/>"
        secoes = [{
            "id": "s1", "codigo": "1", "titulo": "Leitura", "texto": "Texto <x>",
            "tipo": "sim_nao", "ordem": 0,
        }]
        tpl = SimpleNamespace(is_interativo=True, introducao="Intro <y>", secoes=secoes)
        termo = SimpleNamespace(
            status_assinatura_termo="pendente",
            respostas_interativo={"s1": {"sim_nao": "sim", "duvidas": payload}},
            conteudo_termo="",
        )
        consulta = MagicMock()
        procedure = MagicMock()
        with (
            patch(
                "clinica_beleza.termos_consentimento_service.template_do_procedimento",
                return_value=tpl,
            ),
            patch(
                "clinica_beleza.consentimento_service.renderizar_texto_termo",
                side_effect=lambda t, *_a, **_k: t,
            ),
            patch(
                "clinica_beleza.termos_consentimento_service.normalizar_secoes",
                return_value=secoes,
            ),
        ):
            _build_conteudo_texto_termo(elements, termo, consulta, procedure, body_style)

        textos = []
        for el in elements:
            if isinstance(el, Paragraph):
                textos.append(el.text)
        junto = "\n".join(textos)
        self.assertNotIn("<img", junto)
        self.assertNotIn("<b>aberto</b>", junto)
        self.assertIn("&lt;b&gt;aberto&lt;/b&gt;", junto)
        self.assertIn("&lt;img", junto)
