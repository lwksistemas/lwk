"""Leitura da tabela comercial em PDF para o catálogo do CRM."""
from pathlib import Path

from django.test import SimpleTestCase

from crm_vendas.catalogo_pdf import parse_linhas_tabela_comercial, pastas_do_item, preview_catalogo_pdf

_PDF_ANADEM = Path(
    "/home/luiz/.cursor/projects/home-luiz-Documentos-lwksistemas/attachments/"
    "6cdbc61c-6efe-49d0-a172-2285097cc32a/ANADEM-TABELA-COMERCIAL-2026__1_.pdf"
)

_LINHAS_BLUE = [
    "TABELA BLUE 2026",
    "01/01/2026 A 31/12/2026",
    "MEDICINA",
    "ESPECIALIDADESGRUPO",
    "ACUPUNTURA1 ANGIOLOGIA2",
    "CARTÃO DE CRÉDITO",
    "CAPITAL SEGURADO R$ 300.000,00",
    "GRUPO 1 2",
    "R$ 349,00 R$ 399,00 MENSALIDADE",
    "EXTENSÃO PESSOA JURÍDICA",
    "GRUPO 1 2",
    "R$ 349,00 R$ 399,00 MENSALIDADE",
    "EXTENSÃO PJ R$ 174,50 R$ 199,50",
    "R$ 523,50 R$ 598,50 SOMATÓRIA",
]


class CatalogoPdfTabelaTests(SimpleTestCase):
    def test_blue_separa_mensalidade_e_extensao_e_ignora_somatoria(self):
        itens, avisos = parse_linhas_tabela_comercial(_LINHAS_BLUE)
        por_codigo = {item["codigo"]: item for item in itens}

        self.assertEqual(avisos, [])
        self.assertEqual(por_codigo["BLU26-MED-CC-300-1-PF-MEN"]["preco"], "349.00")
        self.assertEqual(por_codigo["BLU26-MED-CC-300-1-XPJ-MEN"]["preco"], "174.50")
        self.assertEqual(por_codigo["BLU26-MED-CC-300-1-PF-MEN"]["recorrencia"], "mensal")
        self.assertEqual(pastas_do_item(por_codigo["BLU26-MED-CC-300-1-PF-MEN"]), ["MEDICINA", "TABELA BLUE"])
        self.assertIn("ACUPUNTURA", por_codigo["BLU26-MED-CC-300-1-PF-MEN"]["descricao"])
        self.assertNotIn("ANGIOLOGIA", por_codigo["BLU26-MED-CC-300-1-PF-MEN"]["descricao"])
        self.assertFalse(any("523.50" == item["preco"] for item in itens))

    def test_pdf_anadem_quando_o_arquivo_esta_disponivel(self):
        if not _PDF_ANADEM.is_file():
            self.skipTest("PDF da tabela ANADEM não está nesta máquina.")
        resultado = preview_catalogo_pdf(_PDF_ANADEM.read_bytes())
        por_codigo = {item["codigo"]: item for item in resultado["itens"]}

        self.assertGreater(resultado["total"], 100)
        self.assertEqual(por_codigo["BLU26-MED-CC-300-1-PF-MEN"]["preco"], "349.00")
        self.assertEqual(por_codigo["GRN26-MED-CC-500-1-PF-MEN"]["preco"], "483.00")
        self.assertEqual(por_codigo["GRN26-MED-BOL-500-1-PF-MEN"]["preco"], "531.30")
        self.assertEqual(por_codigo["ESS26-MED-CC-300-PL-PF-MEN"]["preco"], "399.00")
        self.assertNotIn("retroatividade", por_codigo["ESS26-MED-CC-300-PL-PF-MEN"]["nome"])
        self.assertIn("retroatividade", por_codigo["BLKR26-MED-CC-500-1-PF-MEN"]["nome"])
        self.assertEqual(por_codigo["GRN26-ODO-CC-500-D1-PF-MEN"]["preco"], "257.25")
