"""POST autenticado só pelo cookie exige Origin ou Referer da lista de CORS."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from core.auth_cookies import ACCESS_COOKIE
from superadmin.authentication import SessionAwareJWTAuthentication

ORIGENS = [
    "https://lwksistemas.com.br",
    "https://www.lwksistemas.com.br",
]


@override_settings(CORS_ALLOWED_ORIGINS=ORIGENS)
class OrigemDoCookieTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.auth = SessionAwareJWTAuthentication()

    def pedido(self, method, *, origem=None, referer=None, cookie=None, bearer=None, path="/api/auth/logout/"):
        extra = {}
        if origem is not None:
            extra["HTTP_ORIGIN"] = origem
        if referer is not None:
            extra["HTTP_REFERER"] = referer
        if bearer:
            extra["HTTP_AUTHORIZATION"] = f"Bearer {bearer}"
        bruto = getattr(self.factory, method.lower())(path, **extra)
        if cookie is not None:
            bruto.COOKIES[ACCESS_COOKIE] = cookie
        return Request(bruto)

    def test_site_e_www_autenticam_o_post_com_cookie(self):
        usuario = MagicMock()
        for origem in ORIGENS:
            with patch.object(JWTAuthentication, "authenticate", return_value=(usuario, "tok")):
                resultado = self.auth.authenticate(self.pedido("post", origem=origem, cookie="token-falso"))
            self.assertEqual(resultado[0], usuario)

    def test_referer_do_site_substitui_origin_ausente(self):
        usuario = MagicMock()
        with patch.object(JWTAuthentication, "authenticate", return_value=(usuario, "tok")):
            resultado = self.auth.authenticate(self.pedido(
                "post",
                referer="https://lwksistemas.com.br/loja/demo/dashboard",
                cookie="token-falso",
            ))
        self.assertEqual(resultado[0], usuario)

    def test_beta_evil_e_sem_origem_recebem_403(self):
        casos = [
            {"origem": "https://beta.lwksistemas.com.br"},
            {"origem": "http://beta.lwksistemas.com.br"},
            {"origem": "https://evil.example"},
            {"origem": "https://lwksistemas.com.br.evil.example"},
            {"origem": "null"},
            {},
            {"referer": "https://evil.example/form"},
        ]
        for extra in casos:
            with (
                patch.object(JWTAuthentication, "authenticate") as jwt,
                self.assertRaises(PermissionDenied) as erro,
            ):
                self.auth.authenticate(self.pedido("post", cookie="token-falso", **extra))
            self.assertEqual(erro.exception.status_code, 403)
            jwt.assert_not_called()

    def test_get_de_fora_ainda_autentica(self):
        usuario = MagicMock()
        with patch.object(JWTAuthentication, "authenticate", return_value=(usuario, "tok")):
            resultado = self.auth.authenticate(self.pedido(
                "get",
                origem="https://evil.example",
                cookie="token-falso",
            ))
        self.assertEqual(resultado[0], usuario)

    def test_bearer_copiado_do_cookie_ainda_exige_origem(self):
        pedido = self.pedido(
            "post",
            origem="https://evil.example",
            bearer="token-falso",
            cookie="token-falso",
        )
        pedido.lwk_token_veio_do_cookie = True
        with (
            patch.object(JWTAuthentication, "authenticate") as jwt,
            self.assertRaises(PermissionDenied) as erro,
        ):
            self.auth.authenticate(pedido)
        self.assertEqual(erro.exception.status_code, 403)
        jwt.assert_not_called()

    def test_bearer_copiado_do_cookie_no_site_autentica(self):
        usuario = MagicMock()
        pedido = self.pedido(
            "post",
            origem="https://lwksistemas.com.br",
            bearer="token-falso",
            cookie="token-falso",
        )
        pedido.lwk_token_veio_do_cookie = True
        with patch.object(JWTAuthentication, "authenticate", return_value=(usuario, "tok")):
            resultado = self.auth.authenticate(pedido)
        self.assertEqual(resultado[0], usuario)

    def test_bearer_explicito_ignora_a_origem(self):
        usuario = MagicMock()
        with patch.object(JWTAuthentication, "authenticate", return_value=(usuario, "tok")):
            resultado = self.auth.authenticate(self.pedido(
                "post",
                origem="https://evil.example",
                bearer="token-falso",
                cookie="token-falso",
            ))
        self.assertEqual(resultado[0], usuario)

    def test_sem_credencial_nao_autentica(self):
        self.assertIsNone(self.auth.authenticate(self.pedido("post", origem="https://evil.example")))

    def test_token_invalido_no_site_nao_vira_403(self):
        with self.assertRaises(InvalidToken):
            self.auth.authenticate(self.pedido(
                "post",
                origem="https://lwksistemas.com.br",
                cookie="token-falso",
            ))
