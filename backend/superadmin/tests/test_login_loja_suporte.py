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

    def test_cadastro_nao_assume_conta_de_profissional_ou_vendedor(self):
        """Regressão A1: cadastro público não pode redefinir senha/e-mail de usuário vinculado."""
        from superadmin.models import ProfissionalUsuario, VendedorUsuario

        for nome, modelo, campo in (
            ("prof-vitima", ProfissionalUsuario, "professional_id"),
            ("vend-vitima", VendedorUsuario, "vendedor_id"),
        ):
            vitima = User.objects.create_user(nome, f"{nome}@lwk.test", "senha-original")
            loja = Loja.objects.first()
            modelo.objects.create(user=vitima, loja=loja, **{campo: 1})
            with self.assertRaises(ValidationError):
                LojaCreationService.criar_ou_atualizar_owner(
                    nome, "atacante@lwk.test", "senha-atacante", "A", "B",
                )
            vitima.refresh_from_db()
            self.assertTrue(vitima.check_password("senha-original"))
            self.assertEqual(vitima.email, f"{nome}@lwk.test")

    def test_cadastro_nao_reusa_usuario_de_suporte(self):
        livre = User.objects.create_user("suporte-livre", "livre@lwk.test", "senha-teste")
        UsuarioSistema.objects.create(user=livre, tipo="suporte", is_active=True)
        with self.assertRaises(ValidationError):
            LojaCreationService.criar_ou_atualizar_owner(
                "suporte-livre", "novo@lwk.test", "outra-senha", "Novo", "Dono",
            )
