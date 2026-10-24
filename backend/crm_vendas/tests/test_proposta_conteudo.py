"""A descrição do serviço escolhido entra no conteúdo da proposta."""
from django.test import SimpleTestCase

from crm_vendas.pdf_proposta_contrato.formatters import conteudo_com_descricoes


class _Produto:
    def __init__(self, descricao):
        self.descricao = descricao


class _Item:
    def __init__(self, descricao):
        self.produto_servico = _Produto(descricao)


class _Itens:
    def __init__(self, itens):
        self._itens = itens

    def select_related(self, *_args):
        return self

    def all(self):
        return self._itens


class _Oportunidade:
    def __init__(self, descricoes):
        self.itens = _Itens([_Item(texto) for texto in descricoes])


class ConteudoPropostaTests(SimpleTestCase):
    def test_descricao_do_servico_entra_no_conteudo(self):
        descricao = (
            "ANADEM GREEN 2026. Medicina. Pessoa física. 4 parcelas. "
            "Especialidades: ACUPUNTURA, ALERGIA E IMUNOLOGIA."
        )
        texto = conteudo_com_descricoes("Condições gerais.", _Oportunidade([descricao]))
        self.assertIn("Condições gerais.", texto)
        self.assertIn("ACUPUNTURA, ALERGIA E IMUNOLOGIA.", texto)

    def test_nao_repete_descricao_ja_gravada(self):
        descricao = "ANADEM GREEN 2026. Medicina. Pessoa física."
        self.assertEqual(
            conteudo_com_descricoes(descricao, _Oportunidade([descricao])),
            descricao,
        )

    def test_rotulo_curto_do_plano_sai_do_conteudo(self):
        base = "Prazo de Liberação: acesso em até 24 horas."
        texto = conteudo_com_descricoes(
            f"{base}\n\nUltrasis Laudos - Mensal",
            _Oportunidade(["Ultrasis Laudos - Mensal"]),
        )
        self.assertEqual(texto, base)
        self.assertNotIn("Ultrasis Laudos - Mensal", texto)
