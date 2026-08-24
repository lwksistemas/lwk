from datetime import date
from types import SimpleNamespace

from clinica_geral.perfil_service import aplicar_perfil, serializar_perfil


class _User:
    def __init__(self):
        self.username = "clinicageral"
        self.email = "a@b.com"
        self.first_name = "Luiz"
        self.last_name = "Henrique Felix"
        self.saved = None

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, update_fields=None):
        self.saved = update_fields


def test_serializar_perfil_mostra_nao_informado():
    user = _User()
    perfil = SimpleNamespace(
        tratamento="",
        celular="(16) 99962-1823",
        telefone="",
        conselho="",
        uf="",
        rg="",
        cpf="",
        data_nascimento=None,
        nacionalidade="",
        sexo="",
        cbo="",
        estado_civil="",
        foto_url="",
    )
    dados = serializar_perfil(user, perfil)
    assert dados["nome"] == "Luiz Henrique Felix"
    assert dados["email"] == "a@b.com"
    assert dados["celular"] == "(16) 99962-1823"
    assert dados["sexo_label"] == "Não informado"
    assert dados["estado_civil_label"] == "Não informado"
    assert dados["data_nascimento"] == ""


def test_aplicar_perfil_atualiza_nome_e_nascimento():
    user = _User()
    perfil = SimpleNamespace(
        tratamento="",
        celular="",
        telefone="",
        conselho="",
        uf="",
        rg="",
        cpf="",
        data_nascimento=None,
        nacionalidade="",
        sexo="",
        cbo="",
        estado_civil="",
        foto_url="",
        saved=False,
    )

    def save():
        perfil.saved = True

    perfil.save = save
    aplicar_perfil(
        user,
        perfil,
        {
            "nome": "Ana Lima",
            "email": "ana@clinica.test",
            "sexo": "F",
            "uf": "sp",
            "data_nascimento": "1990-05-20",
        },
    )
    assert user.first_name == "Ana"
    assert user.last_name == "Lima"
    assert user.email == "ana@clinica.test"
    assert user.saved == ["first_name", "last_name", "email"]
    assert perfil.sexo == "F"
    assert perfil.uf == "SP"
    assert perfil.data_nascimento == date(1990, 5, 20)
    assert perfil.saved is True
