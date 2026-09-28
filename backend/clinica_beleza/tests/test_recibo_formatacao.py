"""Testes unitários do recibo (rótulo CPF/CNPJ, telefone, desconto em notes)."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.recibo_service import (
    _extrair_desconto_notes,
    _label_documento_loja,
    _linha_documento_loja,
)
from clinica_beleza.recibo.context import desconto_concedido


class ReciboDocumentoLabelTest(SimpleTestCase):
    def test_cpf_vs_cnpj(self):
        self.assertEqual(_label_documento_loja("12345678901"), "CPF")
        self.assertEqual(_label_documento_loja("12345678000199"), "CNPJ")
        self.assertEqual(_label_documento_loja(""), "CPF/CNPJ")

    def test_linha_documento(self):
        ctx = {
            "loja_documento": "123.456.789-01",
            "loja_documento_label": "CPF",
        }
        self.assertEqual(_linha_documento_loja(ctx), "CPF: 123.456.789-01")


class ReciboDescontoNotesTest(SimpleTestCase):
    def test_extrai_desconto(self):
        payment = SimpleNamespace(notes="Desconto: R$ 200.00")
        self.assertEqual(_extrair_desconto_notes(payment), 200.0)

    def test_sem_desconto(self):
        payment = SimpleNamespace(notes=None)
        self.assertEqual(_extrair_desconto_notes(payment), 0.0)


class DescontoConcedidoTest(SimpleTestCase):
    def test_usa_campo_desconto(self):
        payment = SimpleNamespace(desconto=80, notes="Desconto: R$ 10.00")
        self.assertEqual(desconto_concedido(payment), 80.0)

    def test_cai_para_notes_quando_campo_zero(self):
        payment = SimpleNamespace(desconto=0, notes="Desconto: R$ 200.00")
        self.assertEqual(desconto_concedido(payment), 200.0)


class ReciboMoedaEContaTests(SimpleTestCase):
    def test_formata_milhar_brasileiro(self):
        from clinica_beleza.recibo.moeda import formatar_moeda_recibo

        self.assertEqual(formatar_moeda_recibo(1272.67), "R$ 1.272,67")
        self.assertEqual(formatar_moeda_recibo(200), "R$ 200,00")
        self.assertEqual(formatar_moeda_recibo(0), "R$ 0,00")

    def test_abatimento_explica_item_fora_do_total(self):
        from clinica_beleza.recibo.context import _linhas_descontos_recibo, reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": True,
            "taxa_consulta": 0,
            "taxa_consulta_referencia": 150,
            "desconto_retorno": 150,
            "desconto": 0,
            "procedimentos": [
                {"nome": "TIRZEPATIDA (DOSE MINIMA)", "valor": 300},
                {"nome": "SONO E RELAXAMENTO", "valor": 310},
                {"nome": "BIOESTIMULADOR DE COLÁGENO", "valor": 1800},
            ],
            "subtotal": 2560,
            "valor_total": 610,
            "valor_pago": 300,
            "saldo_devedor": 310,
        })
        self.assertEqual(ctx["valor_total"], 610)
        self.assertEqual(ctx["abatimento"], 1800)
        self.assertEqual(ctx["abatimento_label"], "Abatimento — BIOESTIMULADOR DE COLÁGENO")
        linhas = _linhas_descontos_recibo(ctx)
        self.assertIn(("Desconto retorno", 150), linhas)
        self.assertIn(("Abatimento — BIOESTIMULADOR DE COLÁGENO", 1800), linhas)
        soma_descontos = sum(valor for _label, valor in linhas)
        self.assertEqual(round(ctx["subtotal"] - soma_descontos, 2), 610)
