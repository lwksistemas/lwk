"""Regras puras da venda de produto. Não grava loja, saldo nem financeiro."""
import ast
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from clinica_beleza.venda_produto_service import (
    VendaProdutoError,
    linha_recibo,
    nome_exibicao_venda,
    fechamento_automatico,
    gravar_quem_recebeu,
    nome_operador_caixa,
    usuario_pode_fechar_caixa,
    nome_operador_pagamento,
    pessoa_recibo,
    subtotal_item,
    totais_gaveta,
    totais_sessao_caixa,
    validar_item_venda,
)


class _Vendas:
    def __init__(self, itens):
        self.itens = itens

    def select_related(self, *_args, **_kwargs):
        return self

    def exclude(self, **kwargs):
        status = kwargs.get("status")
        return [item for item in self.itens if item.status != status]


def _produto(**kwargs):
    base = {"nome": "Serum", "is_active": True, "vende_ao_cliente": True, "preco_venda": Decimal("80"), "quantidade_atual": Decimal("10")}
    base.update(kwargs)
    return SimpleNamespace(**base)


class OperadorCaixaFinanceiroTest(unittest.TestCase):
    def test_financeiro_usa_o_operador_escolhido_no_caixa(self):
        sessao = SimpleNamespace(responsavel_nome="LUIZ HENRIQUE FELIX", operador_nome="login")
        self.assertEqual(nome_operador_caixa(sessao), "LUIZ HENRIQUE FELIX")
        self.assertEqual(nome_operador_caixa(None), "")
        venda = SimpleNamespace(operador_nome="LUIZ HENRIQUE FELIX")
        pagamento_produto = SimpleNamespace(venda_balcao=venda, operador_nome="")
        self.assertEqual(nome_operador_pagamento(pagamento_produto), "LUIZ HENRIQUE FELIX")
        atendimento = SimpleNamespace(venda_balcao=None, operador_nome="LUIZ HENRIQUE FELIX")
        self.assertEqual(nome_operador_pagamento(atendimento), "LUIZ HENRIQUE FELIX")
        sem_caixa = SimpleNamespace(venda_balcao=None, operador_nome="")
        self.assertEqual(nome_operador_pagamento(sem_caixa), "")


class QuemRecebeuTest(unittest.TestCase):
    def _pagamento(self, nome=""):
        saved = {}

        class Pagamento:
            operador_nome = nome
            operador_id = None

            def save(self, update_fields=None):
                saved["nome"] = self.operador_nome
                saved["id"] = self.operador_id

        return Pagamento(), saved

    def _usuario(self):
        return SimpleNamespace(
            is_authenticated=True, pk=9, username="admin", get_full_name=lambda: "LUIZ HENRIQUE FELIX",
        )

    def test_consulta_grava_quem_esta_logado(self):
        pagamento, saved = self._pagamento()
        gravar_quem_recebeu(pagamento, origem="consulta", usuario=self._usuario())
        self.assertEqual(saved["nome"], "LUIZ HENRIQUE FELIX")
        self.assertEqual(saved["id"], 9)

    def test_financeiro_grava_quem_confirmou(self):
        pagamento, saved = self._pagamento()
        gravar_quem_recebeu(pagamento, origem="financeiro", usuario=self._usuario())
        self.assertEqual(saved["nome"], "LUIZ HENRIQUE FELIX")
        self.assertEqual(saved["id"], 9)

    def test_sem_usuario_nao_grava_nome(self):
        pagamento, saved = self._pagamento()
        gravar_quem_recebeu(pagamento, origem="consulta", usuario=None)
        self.assertEqual(saved, {})
        self.assertEqual(pagamento.operador_nome, "")

    def test_nao_troca_nome_ja_gravado(self):
        pagamento, saved = self._pagamento("CAIXA")
        gravar_quem_recebeu(pagamento, origem="financeiro", usuario=self._usuario())
        self.assertEqual(saved, {})
        self.assertEqual(pagamento.operador_nome, "CAIXA")


class FecharCaixaDoOperadorTest(unittest.TestCase):
    def test_outro_login_nao_fecha_o_caixa_da_bruna(self):
        sessao = SimpleNamespace(
            responsavel_nome="BRUNA TUCCI MARTINS",
            operador_nome="BRUNA TUCCI MARTINS",
            responsavel_id=None,
        )
        luiz = SimpleNamespace(is_authenticated=True, pk=9, email="", username="luiz", get_full_name=lambda: "LUIZ HENRIQUE FELIX")
        bruna = SimpleNamespace(is_authenticated=True, pk=3, email="", username="bruna", get_full_name=lambda: "bruna tucci martins")
        self.assertFalse(usuario_pode_fechar_caixa(sessao, luiz))
        self.assertTrue(usuario_pode_fechar_caixa(sessao, bruna))

    def test_caixa_esquecido_fecha_depois_das_23_59(self):
        fuso = ZoneInfo("America/Sao_Paulo")
        abertura = datetime(2026, 11, 5, 18, 21, tzinfo=fuso)
        self.assertIsNone(fechamento_automatico(abertura, datetime(2026, 11, 5, 23, 59, 30, tzinfo=fuso)))
        limite = fechamento_automatico(abertura, datetime(2026, 11, 6, 0, 0, tzinfo=fuso))
        self.assertEqual(limite, datetime(2026, 11, 5, 23, 59, 59, tzinfo=fuso))


class VendaProdutoRegrasTest(unittest.TestCase):
    def test_caixa_sem_venda_nao_tem_valor_a_receber(self):
        sessao = SimpleNamespace(status="aberta", vendas=_Vendas([]))
        self.assertEqual(
            totais_sessao_caixa(sessao),
            {"vendas_produtos": 0.0, "recebido": 0.0, "a_receber": 0.0},
        )
        self.assertEqual(
            totais_sessao_caixa(SimpleNamespace(status="fechada", vendas=_Vendas([]))),
            {"vendas_produtos": 0.0, "recebido": 0.0, "a_receber": 0.0},
        )

    def test_caixa_a_prazo_fica_a_receber_na_gaveta(self):
        payment = SimpleNamespace(
            status="PENDING", amount=Decimal("0"), valor_total=Decimal("80"), valor_produtos=Decimal("80"),
        )
        venda = SimpleNamespace(status="concluida", payment=payment)
        totais = totais_sessao_caixa(SimpleNamespace(status="aberta", vendas=_Vendas([venda])))
        self.assertEqual(totais["a_receber"], 80.0)
        self.assertEqual(totais["recebido"], 0.0)
        fechada = totais_gaveta(SimpleNamespace(status="fechada", vendas=_Vendas([venda])))
        self.assertEqual(fechada["a_receber"], 80.0)
        self.assertEqual(
            totais_sessao_caixa(SimpleNamespace(status="fechada", vendas=_Vendas([venda]))),
            {"vendas_produtos": 0.0, "recebido": 0.0, "a_receber": 0.0},
        )
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

    def test_recibo_sem_cadastro_nao_exige_cpf(self):
        sem_nome = SimpleNamespace(paciente=None, nome_cliente="", email_cliente="", telefone_cliente="")
        self.assertEqual(nome_exibicao_venda(sem_nome), "Consumidor não identificado")
        self.assertEqual(pessoa_recibo(sem_nome).cpf, "")
        so_nome = SimpleNamespace(paciente=None, nome_cliente="Maria", email_cliente="a@b.c", telefone_cliente="11999990000")
        self.assertEqual(nome_exibicao_venda(so_nome), "Maria")
        self.assertEqual(pessoa_recibo(so_nome).telefone, "11999990000")
        cadastrado = SimpleNamespace(paciente=SimpleNamespace(nome="Ana"), nome_cliente="Outro")
        self.assertEqual(nome_exibicao_venda(cadastrado), "Ana")
        self.assertIs(pessoa_recibo(cadastrado), cadastrado.paciente)


if __name__ == "__main__":
    unittest.main()
