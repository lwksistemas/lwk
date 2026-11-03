"""Regras puras da venda de produto. Não grava loja, saldo nem financeiro."""
import ast
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from clinica_beleza.venda_produto_service import (
    VendaProdutoError,
    linha_recibo,
    subtotal_item,
    validar_item_venda,
)


def _produto(**kwargs):
    base = {"nome": "Serum", "is_active": True, "vende_ao_cliente": True, "preco_venda": Decimal("80"), "quantidade_atual": Decimal("10")}
    base.update(kwargs)
    return SimpleNamespace(**base)


class VendaProdutoRegrasTest(unittest.TestCase):
    def test_subtotal_separa_desconto_da_linha(self):
        self.assertEqual(subtotal_item("2", "50", "10"), Decimal("90"))
        self.assertEqual(subtotal_item("1", "10", "40"), Decimal("0"))

    def test_linha_do_recibo_traz_nome_quantidade_preco_e_subtotal(self):
        linha = linha_recibo("Protetor", "2", "35.50", "5")
        self.assertEqual(linha["nome"], "Protetor")
        self.assertEqual(linha["quantidade"], "2")
        self.assertEqual(linha["preco_unitario"], 35.5)
        self.assertEqual(linha["subtotal"], 66.0)

    def test_nao_vende_inativo_nem_produto_sem_permissao(self):
        with self.assertRaises(VendaProdutoError):
            validar_item_venda(_produto(is_active=False), 1, [])
        with self.assertRaises(VendaProdutoError):
            validar_item_venda(_produto(vende_ao_cliente=False), 1, [])

    def test_nao_vende_so_com_lote_vencido_nem_acima_do_utilizavel(self):
        hoje = date(2026, 11, 3)
        vencido = [{"quantidade": Decimal("4"), "validade": date(2020, 1, 1)}]
        with self.assertRaises(VendaProdutoError):
            validar_item_venda(_produto(quantidade_atual=Decimal("4")), 1, vencido, hoje=hoje)
        with self.assertRaises(VendaProdutoError):
            validar_item_venda(_produto(quantidade_atual=Decimal("2")), 3, [], hoje=hoje)

    def test_saldo_anterior_sem_lote_continua_vendavel(self):
        validar_item_venda(_produto(quantidade_atual=Decimal("4")), 4, [], hoje=date(2026, 11, 3))

    def test_importacao_de_nota_atualiza_custo_e_nao_o_preco_de_venda(self):
        origem = Path(__file__).resolve().parents[1] / "estoque_xml_import_service.py"
        arvore = ast.parse(origem.read_text(encoding="utf-8"))
        campos = []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Assign) and any(getattr(alvo, "id", "") == "campos" for alvo in no.targets):
                if isinstance(no.value, ast.List):
                    campos = [item.value for item in no.value.elts if isinstance(item, ast.Constant)]
        self.assertIn("preco_custo", campos)
        self.assertNotIn("preco_venda", campos)

    def test_recibo_separa_produto_vendido_do_insumo(self):
        from clinica_beleza.recibo.context import produtos_exibidos_recibo

        linhas = produtos_exibidos_recibo({
            "produtos": [linha_recibo("Protetor", 1, 40, 0)],
            "procedimentos": [{"nome": "Limpeza", "valor": 120}],
        })
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["nome"], "Protetor")
        self.assertEqual(linhas[0]["subtotal"], 40.0)
        self.assertEqual(produtos_exibidos_recibo({"produtos": [], "procedimentos": [{"nome": "Uso interno", "valor": 0}]}), [])


if __name__ == "__main__":
    unittest.main()
