"""O HTML do template perde script e mantém o texto e a formatação."""
from crm_vendas.html_template import limpar_html_template


def test_texto_sem_tag_permanece():
    bruto = "Valor < 10\n[[folha:2]]\n[[letra:times|12]]"
    assert limpar_html_template(bruto) == bruto


def test_script_sai_e_a_formatacao_fica():
    bruto = (
        '<p data-align="center">Investimento [[folha:2]]</p>'
        '<span data-font="times" data-size="12" data-bold="1">Parcela</span>'
        '<script>alert(1)</script>'
        '<p onclick="alert(1)">Texto</p>'
    )
    limpo = limpar_html_template(bruto)
    assert "<script" not in limpo
    assert "alert(1)" not in limpo
    assert "onclick" not in limpo
    assert 'data-align="center"' in limpo
    assert 'data-font="times"' in limpo
    assert 'data-size="12"' in limpo
    assert 'data-bold="1"' in limpo
    assert "[[folha:2]]" in limpo
    assert "Investimento" in limpo
    assert "Parcela" in limpo
    assert "Texto" in limpo
