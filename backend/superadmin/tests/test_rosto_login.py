"""O rosto só libera o login no domínio da LWK e com um desafio de uso único."""

from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase, TestCase
from rest_framework.test import APIClient

from superadmin.rosto_service import RostoErro, _consumir_desafio, _guardar_desafio, origem_confiavel


class RostoOrigemTest(SimpleTestCase):
    def test_producao_e_beta_aceitam_o_proprio_host(self):
        fabrica = RequestFactory()
        rp, origem = origem_confiavel(fabrica.post("/", HTTP_ORIGIN="https://lwksistemas.com.br"))
        self.assertEqual((rp, origem), ("lwksistemas.com.br", "https://lwksistemas.com.br"))
        rp_beta, origem_beta = origem_confiavel(
            fabrica.post("/", HTTP_ORIGIN="https://beta.lwksistemas.com.br"),
        )
        self.assertEqual(rp_beta, "beta.lwksistemas.com.br")
        self.assertEqual(origem_beta, "https://beta.lwksistemas.com.br")

    def test_host_de_fora_recusa(self):
        pedido = RequestFactory().post("/", HTTP_ORIGIN="https://evil.example")
        with self.assertRaises(RostoErro):
            origem_confiavel(pedido)

    def test_desafio_so_vale_uma_vez_e_para_o_mesmo_usuario(self):
        _guardar_desafio(b"desafio-rosto", "entrada", 7, "superadmin")
        with self.assertRaises(RostoErro):
            _consumir_desafio(b"desafio-rosto", "entrada", 8, "superadmin")
        _guardar_desafio(b"desafio-rosto-2", "entrada", 7, "superadmin")
        _consumir_desafio(b"desafio-rosto-2", "entrada", 7, "superadmin")
        with self.assertRaises(RostoErro):
            _consumir_desafio(b"desafio-rosto-2", "entrada", 7, "superadmin")


class RostoLoginApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("comum-rosto", password="senha-teste-123")

    def test_sem_usuario_pede_a_senha(self):
        resposta = self.client.post(
            "/api/auth/rosto/entrar/opcoes/",
            {"username": "ninguem-rosto", "user_type": "superadmin"},
            format="json",
            HTTP_ORIGIN="https://lwksistemas.com.br",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("senha", resposta.data["error"].lower())

    def test_usuario_comum_nao_ativa_rosto_de_superadmin(self):
        self.client.force_authenticate(user=self.user)
        resposta = self.client.post(
            "/api/auth/rosto/registrar/opcoes/",
            {"user_type": "superadmin"},
            format="json",
            HTTP_ORIGIN="https://lwksistemas.com.br",
        )
        self.assertEqual(resposta.status_code, 403)

    def test_entrada_sem_desafio_nao_abre_sessao(self):
        admin = User.objects.create_superuser("admin-rosto", "admin-rosto@example.com", "senha-teste-123")
        resposta = self.client.post(
            "/api/auth/rosto/entrar/",
            {
                "username": admin.username,
                "user_type": "superadmin",
                "credential": {"id": "abc", "response": {}},
            },
            format="json",
            HTTP_ORIGIN="https://lwksistemas.com.br",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertNotIn("access", resposta.data)
