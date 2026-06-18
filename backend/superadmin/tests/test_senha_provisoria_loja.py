from types import SimpleNamespace
from unittest import TestCase

from superadmin.services.login_service import usuario_precisa_trocar_senha_loja


class SenhaProvisoriaLojaTests(TestCase):
    def test_proprietario_com_senha_provisoria(self):
        loja = SimpleNamespace(
            owner_id=1, senha_foi_alterada=False, senha_provisoria='abc123',
        )
        user = SimpleNamespace(id=1)
        self.assertTrue(usuario_precisa_trocar_senha_loja(user, loja))

    def test_proprietario_ja_trocou_senha(self):
        loja = SimpleNamespace(
            owner_id=1, senha_foi_alterada=True, senha_provisoria='abc123',
        )
        user = SimpleNamespace(id=1)
        pu = SimpleNamespace(precisa_trocar_senha=False)
        vu = SimpleNamespace(precisa_trocar_senha=False)
        self.assertFalse(usuario_precisa_trocar_senha_loja(user, loja, pu=pu, vu=vu))

    def test_profissional_precisa_trocar(self):
        loja = SimpleNamespace(owner_id=99, senha_foi_alterada=True, senha_provisoria='')
        user = SimpleNamespace(id=2)
        pu = SimpleNamespace(precisa_trocar_senha=True)
        vu = SimpleNamespace(precisa_trocar_senha=False)
        self.assertTrue(usuario_precisa_trocar_senha_loja(user, loja, pu=pu, vu=vu))

    def test_profissional_ja_trocou(self):
        loja = SimpleNamespace(owner_id=99, senha_foi_alterada=True, senha_provisoria='')
        user = SimpleNamespace(id=2)
        pu = SimpleNamespace(precisa_trocar_senha=False)
        vu = SimpleNamespace(precisa_trocar_senha=False)
        self.assertFalse(usuario_precisa_trocar_senha_loja(user, loja, pu=pu, vu=vu))
