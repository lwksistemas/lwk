"""Fallback de X-Loja-ID / X-Tenant-Slug só com vínculo na loja."""
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase

from clinica_beleza.views_base import resolve_loja_id_from_request
from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class ResolveLojaIdFromRequestTest(TestCase):
    def setUp(self):
        set_current_loja_id(None)
        set_current_tenant_db("default")
        self.factory = RequestFactory()
        tipo = TipoLoja.objects.create(nome="Clínica", slug="clinica-teste-rl", codigo="CTRL")
        plano = PlanoAssinatura.objects.create(nome="Básico", slug="basico-rl", preco_mensal=99)
        self.owner_a = User.objects.create_user(
            username="owner-a-rl@test.com", email="owner-a-rl@test.com", password="senha12345",
        )
        self.owner_b = User.objects.create_user(
            username="owner-b-rl@test.com", email="owner-b-rl@test.com", password="senha12345",
        )
        self.loja_a = Loja.objects.create(
            nome="Loja A RL", slug="loja-a-rl", cpf_cnpj="11111111000191",
            tipo_loja=tipo, plano=plano, owner=self.owner_a, database_name="loja_a_rl",
        )
        self.loja_b = Loja.objects.create(
            nome="Loja B RL", slug="loja-b-rl", cpf_cnpj="22222222000200",
            tipo_loja=tipo, plano=plano, owner=self.owner_b, database_name="loja_b_rl",
        )

    def tearDown(self):
        set_current_loja_id(None)
        set_current_tenant_db("default")

    def _request(self, user, loja_id=None, slug=None):
        headers = {}
        if loja_id is not None:
            headers["HTTP_X_LOJA_ID"] = str(loja_id)
        if slug:
            headers["HTTP_X_TENANT_SLUG"] = slug
        request = self.factory.get("/api/clinica-beleza/pacientes/", **headers)
        request.user = user
        return request

    def test_owner_usa_header_da_propria_loja(self):
        request = self._request(self.owner_a, loja_id=self.loja_a.id)
        self.assertEqual(resolve_loja_id_from_request(request), self.loja_a.id)

    def test_owner_nao_usa_header_de_outra_loja(self):
        request = self._request(self.owner_a, loja_id=self.loja_b.id)
        self.assertIsNone(resolve_loja_id_from_request(request))

    def test_anonimo_nao_resolve_por_header(self):
        request = self._request(AnonymousUser(), loja_id=self.loja_a.id)
        self.assertIsNone(resolve_loja_id_from_request(request))

    def test_slug_de_outra_loja_e_rejeitado(self):
        request = self._request(self.owner_a, slug=self.loja_b.slug)
        self.assertIsNone(resolve_loja_id_from_request(request))

    def test_contexto_do_middleware_prevalece(self):
        set_current_loja_id(self.loja_a.id)
        request = self._request(self.owner_a, loja_id=self.loja_b.id)
        self.assertEqual(resolve_loja_id_from_request(request), self.loja_a.id)
