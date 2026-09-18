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
