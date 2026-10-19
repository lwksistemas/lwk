"""O comprovante só libera quando o PDF é o da loja e o banco devolve um crédito."""
from decimal import Decimal

from django.test import SimpleTestCase

from unittest.mock import patch

from superadmin.comprovante_pagamento import (
    _escolher_cora,
    _escolher_pix_asaas,
    _escolher_transferencia_asaas,
    conferir_cadastro,
    forma_do_comprovante,
    ler_comprovante,
)

E2E = "E12345678202610191200ABCDEFGHIJK"
TEXTO = (
    "Pagador HARMONIS CLINICA\n"
    "CNPJ 37.302.743/0001-99\n"
    f"Valor R$ 99,90\nID {E2E}"
)


class ComprovanteCadastroTest(SimpleTestCase):
    def test_pdf_vazio_nao_passa(self):
        leitura = ler_comprovante(b"%PDF-1.4")
        self.assertFalse(leitura["ok"])

    def test_comprovante_com_codigo_e_pix_e_sem_codigo_e_transferencia(self):
        self.assertEqual(forma_do_comprovante({"e2e": E2E}), "pix")
        self.assertEqual(forma_do_comprovante({"e2e": ""}), "transferencia")
        self.assertEqual(forma_do_comprovante({"e2e": E2E}, "transferencia"), "transferencia")

    def test_foto_usa_o_texto_lido(self):
        from io import BytesIO

        from PIL import Image

        buffer = BytesIO()
        Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")
        with patch("superadmin.comprovante_pagamento._texto_ocr", return_value=TEXTO):
            leitura = ler_comprovante(buffer.getvalue())
        self.assertTrue(leitura["ok"], leitura)
        self.assertEqual(leitura["e2e"], E2E)

    def test_outro_documento_recusa(self):
        resultado = conferir_cadastro(
            {"ok": True, "texto": "OUTRA EMPRESA CNPJ 11.222.333/0001-81 Valor R$ 99,90", "e2e": E2E},
            "HARMONIS",
            "37302743000199",
            Decimal("99.90"),
        )
        self.assertFalse(resultado["ok"])
        self.assertIn("CPF ou CNPJ", resultado["error"])

    def test_mesmo_nome_e_documento_passa(self):
        resultado = conferir_cadastro(
            {"ok": True, "texto": TEXTO, "e2e": E2E},
            "HARMONIS",
            "37302743000199",
            Decimal("99.90"),
        )
        self.assertTrue(resultado["ok"], resultado)

    def test_pix_asaas_exige_o_codigo_e_o_valor(self):
        achado = _escolher_pix_asaas(
            [{
                "id": "pix_1",
                "endToEndIdentifier": E2E,
                "value": 99.9,
                "status": "DONE",
                "type": "CREDIT",
                "externalAccount": {"name": "HARMONIS CLINICA", "cpfCnpj": "***.743/0001-**"},
            }],
            E2E,
            Decimal("99.90"),
            TEXTO,
        )
        self.assertEqual(achado["id"], "pix_1")

        outro_valor = _escolher_pix_asaas(
            [{
                "id": "pix_2",
                "endToEndIdentifier": E2E,
                "value": 7,
                "status": "DONE",
                "type": "CREDIT",
                "externalAccount": {"name": "HARMONIS", "cpfCnpj": "37302743000199"},
            }],
            E2E,
            Decimal("99.90"),
            TEXTO,
        )
        self.assertFalse(outro_valor["ok"])

    def test_transferencia_asaas_com_dois_creditos_nao_escolhe(self):
        lancamentos = [
            {"id": "a", "type": "TRANSFER", "value": 99.9, "description": "HARMONIS"},
            {"id": "b", "type": "TRANSFER", "value": 99.9, "description": "HARMONIS"},
        ]
        resultado = _escolher_transferencia_asaas(lancamentos, Decimal("99.90"), TEXTO)
        self.assertFalse(resultado["ok"])
        sem_nome = _escolher_transferencia_asaas(
            [{"id": "c", "type": "TRANSFER", "value": 99.9, "description": "Transferencia recebida"}],
            Decimal("99.90"),
            TEXTO,
        )
        self.assertFalse(sem_nome["ok"])

    def test_cora_casa_documento_e_valor(self):
        entradas = [{
            "id": "ent_1",
            "type": "CREDIT",
            "amount": 9990,
            "transaction": {
                "id": "trx_1",
                "description": "Pix",
                "counterParty": {"name": "HARMONIS CLINICA", "identity": "37302743000199"},
            },
        }]
        resultado = _escolher_cora(entradas, {"texto": TEXTO, "e2e": ""}, Decimal("99.90"), "37302743000199")
        self.assertEqual(resultado["id"], "ent_1")

        outro_documento = _escolher_cora(
            entradas, {"texto": TEXTO, "e2e": ""}, Decimal("99.90"), "11222333000181",
        )
        self.assertFalse(outro_documento["ok"])
