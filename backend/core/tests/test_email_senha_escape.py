"""Regressão: template HTML de senha provisória escapa dados dinâmicos."""
from django.test import SimpleTestCase

from core.email_templates import email_senha_provisoria_html


class EmailSenhaEscapeTest(SimpleTestCase):
    def test_escapa_nome_loja_e_usuario(self):
        html, _texto = email_senha_provisoria_html(
            nome_destinatario='<img src=x onerror=alert(1)>',
            usuario='admin<script>',
            senha='a<b>1',
            url_login='https://lwksistemas.com.br/login?q="x"',
            titulo_principal='Bem-vindo <b>',
            subtitulo='Sub <i>',
            info_adicional={"Loja": "<loja>"},
            nome_sistema='Sys <xss>',
        )
        self.assertNotIn("<img", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<loja>", html)
        self.assertIn("&lt;img", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;loja&gt;", html)
        self.assertIn("https://lwksistemas.com.br/login?q=&quot;x&quot;", html)
