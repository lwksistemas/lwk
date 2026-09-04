from clinica_geral.equipe_service import cargo_label, normalizar_nome, normalizar_uf


def test_cargo_label_recepcao():
    assert cargo_label("recepcao") == "Recepção"
    assert cargo_label("administracao") == "Administração"
    assert cargo_label("") == "Outros"


def test_normalizar_uf_e_nome():
    assert normalizar_uf(" sp ") == "SP"
    assert normalizar_nome("  Dra. Ana  ") == "Dra. Ana"
