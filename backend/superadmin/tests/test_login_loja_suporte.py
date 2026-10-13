"""Dono da loja que também é suporte entra pelo login da loja."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from superadmin.models import Loja, PlanoAssinatura, TipoLoja, UsuarioSistema
from superadmin.services.login_service import LoginService
from superadmin.services.loja_creation_service import LojaCreationService


class LoginLojaSuporteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("lhfd-teste", "lhfd-teste@lwk.test", "senha-teste")
        UsuarioSistema.objects.create(user=self.user, tipo="suporte", is_active=True)
        tipo = TipoLoja.objects.create(nome="Clínica Login", slug="clinica-login", codigo="CLILOG")
        plano = PlanoAssinatura.objects.create(
            nome="Básico Log", slug="basico-log", descricao="Básico", preco_mensal="99.90",
        )
        plano.tipos_loja.add(tipo)
        Loja.objects.create(
            nome="Clinica Teste",
            slug="34787081845000",
            atalho="felipe-teste",
            cpf_cnpj="34787081845",
            tipo_loja=tipo,
            plano=plano,
            owner=self.user,
        )
        self.service = LoginService()

    def test_login_da_loja_trata_como_loja(self):
        self.assertEqual(self.service._get_user_type(self.user, "felipe-teste"), "loja")

    def test_sem_loja_continua_suporte(self):
        self.assertEqual(self.service._get_user_type(self.user, None), "suporte")

    def test_cadastro_nao_reusa_usuario_de_suporte(self):
        livre = User.objects.create_user("suporte-livre", "livre@lwk.test", "senha-teste")
        UsuarioSistema.objects.create(user=livre, tipo="suporte", is_active=True)
        with self.assertRaises(ValidationError):
            LojaCreationService.criar_ou_atualizar_owner(
                "suporte-livre", "novo@lwk.test", "outra-senha", "Novo", "Dono",
            )
