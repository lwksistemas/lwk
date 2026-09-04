"""Testes do TenantMiddleware._slug_from_subdomain.

Garante que subdomínios reservados de infraestrutura (api, www, media, etc.)
não sejam tratados como slug de loja — o que gerava warnings "Loja não
encontrada: api" a cada chamada SSR do frontend (host api.<dominio>).
"""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from tenants.middleware import TenantMiddleware


def _request(host: str):
    request = MagicMock()
    request.get_host.return_value = host
    # Usuário anônimo: _slug_from_subdomain não faz validação de dono nesse caso.
    request.user.is_authenticated = False
    return request


class SlugFromSubdomainTests(SimpleTestCase):
    def setUp(self):
        self.mw = TenantMiddleware(get_response=lambda r: r)

    def test_subdominio_api_e_ignorado(self):
        self.assertIsNone(self.mw._slug_from_subdomain(_request("api.lwksistemas.com.br")))

    def test_subdominios_infra_sao_ignorados(self):
        for host in (
            "www.lwksistemas.com.br",
            "media.lwksistemas.com.br",
            "static.lwksistemas.com.br",
            "cdn.lwksistemas.com.br",
        ):
            with self.subTest(host=host):
                self.assertIsNone(self.mw._slug_from_subdomain(_request(host)))

    def test_dominio_publico_configurado_nao_gera_slug(self):
        # Com LWK_PUBLIC_DOMAIN setado (produção), o domínio raiz é ignorado
        # mesmo tendo 3 partes (ex.: lwksistemas.com.br).
        with self.settings():
            import os
            os.environ["LWK_PUBLIC_DOMAIN"] = "lwksistemas.com.br"
            try:
                self.assertIsNone(
                    self.mw._slug_from_subdomain(_request("lwksistemas.com.br")),
                )
            finally:
                os.environ.pop("LWK_PUBLIC_DOMAIN", None)

    def test_subdominio_de_loja_real_vira_slug(self):
        # Um subdomínio que não é reservado deve ser considerado slug de loja
        # (usuário anônimo, sem validação de dono).
        self.assertEqual(
            self.mw._slug_from_subdomain(_request("clinicaharmonis.lwksistemas.com.br")),
            "clinicaharmonis",
        )
