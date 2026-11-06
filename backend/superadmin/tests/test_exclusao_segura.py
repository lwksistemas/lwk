"""Exclusão de usuário e de loja pede confirmação e não apaga o histórico."""
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from superadmin.exclusao_segura import confirmacao_confere, eh_ultimo_superadmin_ativo
from superadmin.models import HistoricoAcessoGlobal, UsuarioSistema
from superadmin.views.usuarios import UsuarioSistemaViewSet


class ConfirmacaoExclusaoTest(TestCase):
    def test_sem_o_identificador_nao_confirma(self):
        request = SimpleNamespace(data={})
        self.assertFalse(confirmacao_confere(request, "felix"))

    def test_o_identificador_confirma(self):
        request = SimpleNamespace(data={"confirmacao": "felix"})
        self.assertTrue(confirmacao_confere(request, "felix"))

    def test_ultimo_superadmin_ativo_nao_sai(self):
        user = User.objects.create_user(username="unico", email="unico@lwk.test", password="x")
        perfil = UsuarioSistema.objects.create(user=user, tipo="superadmin", is_active=True)
        self.assertTrue(eh_ultimo_superadmin_ativo(perfil))
        outro = User.objects.create_user(username="outro", email="outro@lwk.test", password="x")
        UsuarioSistema.objects.create(user=outro, tipo="superadmin", is_active=True)
        self.assertFalse(eh_ultimo_superadmin_ativo(perfil))


class ExclusaoUsuarioViewTest(TestCase):
    def setUp(self):
        self.ator = User.objects.create_superuser("ator", "ator@lwk.test", "x")
        UsuarioSistema.objects.create(user=self.ator, tipo="superadmin", is_active=True)
        self.alvo_user = User.objects.create_user("alvo", "alvo@lwk.test", "x")
        self.alvo = UsuarioSistema.objects.create(user=self.alvo_user, tipo="suporte", is_active=True)
        HistoricoAcessoGlobal.objects.create(
            user=self.alvo_user,
            usuario_email="alvo@lwk.test",
            usuario_nome="Alvo",
            acao="login",
            ip_address="203.0.113.9",
        )

    def _apagar(self, dados):
        factory = APIRequestFactory()
        request = factory.delete("/", dados, format="json")
        force_authenticate(request, self.ator)
        view = UsuarioSistemaViewSet.as_view({"delete": "destroy"})
        return view(request, pk=self.alvo.id)

    def test_sem_confirmacao_o_usuario_continua(self):
        resposta = self._apagar({})
        self.assertEqual(resposta.status_code, 400)
        self.assertTrue(UsuarioSistema.objects.filter(id=self.alvo.id).exists())

    def test_com_confirmacao_o_historico_fica(self):
        resposta = self._apagar({"confirmacao": "alvo"})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="alvo").exists())
        self.assertTrue(
            HistoricoAcessoGlobal.objects.filter(usuario_email="alvo@lwk.test", acao="login").exists()
        )
        self.assertTrue(
            HistoricoAcessoGlobal.objects.filter(acao="excluir", recurso="UsuarioSistema").exists()
        )
