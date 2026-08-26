from clinica_beleza.agenda_service import versao_int


def test_versao_int_aceita_string_e_int():
    assert versao_int(5) == 5
    assert versao_int("5") == 5
    assert versao_int(None) is None
    assert versao_int("") is None
    assert versao_int("x") is None
