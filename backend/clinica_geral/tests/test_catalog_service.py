from clinica_geral.catalog_service import montar_endereco, slug_codigo


def test_slug_codigo_remove_acento():
    assert slug_codigo("Primeira consulta") == "primeira_consulta"
    assert slug_codigo("Retorno") == "retorno"
    assert slug_codigo("  ") == "tipo"


def test_montar_endereco_junta_partes():
    texto = montar_endereco(
        logradouro="Rua A",
        numero="10",
        bairro="Centro",
        cidade="Ribeirão Preto",
        uf="sp",
        cep="14000-000",
    )
    assert texto == "Rua A, 10, Centro, Ribeirão Preto, SP, 14000-000"
    assert montar_endereco() == ""


def test_montar_endereco_ignora_vazios():
    assert montar_endereco(cidade="Ribeirão Preto", uf="SP") == "Ribeirão Preto, SP"
