from clinica_geral.alergia_service import medicamento_conflita_alergia, tokens_alergia


def test_tokens_e_conflito_de_alergia():
    assert "dipirona" in tokens_alergia("Dipirona, penicilina")
    assert medicamento_conflita_alergia("dipirona, AAS", "Dipirona 500mg")
    assert not medicamento_conflita_alergia("penicilina", "paracetamol 750")
