from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from crm_vendas.midia_documentos import arquivar_pdf_assinado, documento_do_cliente


class MidiaDocumentosTests(SimpleTestCase):
    def test_empresa_usa_o_cnpj_da_conta(self):
        documento = SimpleNamespace(
            oportunidade=SimpleNamespace(
                lead=SimpleNamespace(
                    cpf_cnpj="123.456.789-09",
                    conta=SimpleNamespace(cnpj="08.961.407/0008-63"),
                )
            )
        )
        self.assertEqual(documento_do_cliente(documento), "08961407000863")

    def test_pessoa_fisica_usa_o_cpf_do_lead(self):
        documento = SimpleNamespace(
            oportunidade=SimpleNamespace(
                lead=SimpleNamespace(cpf_cnpj="123.456.789-09", conta=None)
            )
        )
        self.assertEqual(documento_do_cliente(documento), "12345678909")

    @patch("core.media_pdf.salvar_pdf_pasta")
    def test_arquiva_no_cliente_e_na_prestadora(self, mock_salvar):
        documento = SimpleNamespace(
            loja_id=4,
            oportunidade=SimpleNamespace(
                lead=SimpleNamespace(cpf_cnpj="12345678909", conta=None),
                empresa_prestadora=SimpleNamespace(cnpj="38.900.437/0001-54"),
            ),
        )
        arquivar_pdf_assinado(documento, b"%PDF", "proposta_1_assinado.pdf")
        pastas = [chamada.args[1] for chamada in mock_salvar.call_args_list]
        self.assertEqual(
            pastas,
            ["documentos/12345678909", "prestadoras/38900437000154"],
        )
