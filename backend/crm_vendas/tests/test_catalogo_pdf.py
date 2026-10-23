"""Leitura da tabela comercial em PDF para o catálogo do CRM."""
from pathlib import Path

from django.test import SimpleTestCase

from crm_vendas.catalogo_pdf import (
    _parse_catalogo_pipe,
    encurtar_codigo_anadem,
    parse_linhas_tabela_comercial,
    pasta_do_pagamento,
    pasta_do_produto,
    pastas_do_item,
    preview_catalogo_pdf,
)
from crm_vendas.pdf_proposta_contrato.sections import nome_item_documento

_PDF_ULTRASIS = Path(
    "/home/luiz/.cursor/projects/home-luiz-Documentos-lwksistemas/attachments/"
    "6cdbc61c-6efe-49d0-a172-2285097cc32a/ULTRASIS_Produtos_Importacao.pdf"
)

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
        self.assertEqual(por_codigo["B26MC3-1FM"]["preco"], "349.00")
        self.assertEqual(por_codigo["B26MC3-1FM"]["codigo_anterior"], "BLU26-MED-CC-300-1-PF-MEN")
        self.assertEqual(por_codigo["B26MC3-1XM"]["preco"], "174.50")
        self.assertEqual(por_codigo["B26MC3-1FM"]["recorrencia"], "mensal")
        self.assertEqual(por_codigo["B26MC3-1FM"]["grupo"], "1")
        self.assertEqual(por_codigo["B26MC3-1FM"]["pagamento"], "CC")
        self.assertEqual(
            pastas_do_item(por_codigo["B26MC3-1FM"]),
            ["MEDICINA", "TABELA BLUE", "GRUPO 1", "CARTÃO DE CRÉDITO"],
        )
        self.assertEqual(
            pastas_do_item(por_codigo["B26MC3-2FM"]),
            ["MEDICINA", "TABELA BLUE", "GRUPO 2", "CARTÃO DE CRÉDITO"],
        )
        self.assertIn("ACUPUNTURA", por_codigo["B26MC3-1FM"]["descricao"])
        self.assertNotIn("ANGIOLOGIA", por_codigo["B26MC3-1FM"]["descricao"])
        self.assertFalse(any("523.50" == item["preco"] for item in itens))

    def test_pdf_anadem_quando_o_arquivo_esta_disponivel(self):
        if not _PDF_ANADEM.is_file():
            self.skipTest("PDF da tabela ANADEM não está nesta máquina.")
        resultado = preview_catalogo_pdf(_PDF_ANADEM.read_bytes())
        por_codigo = {item["codigo"]: item for item in resultado["itens"]}

        self.assertGreater(resultado["total"], 100)
        self.assertEqual(por_codigo["B26MC3-1FM"]["preco"], "349.00")
        self.assertEqual(por_codigo["G26MC5-1FM"]["preco"], "483.00")
        self.assertEqual(por_codigo["G26MB5-1FM"]["preco"], "531.30")
        self.assertEqual(por_codigo["E26MC3-PLFM"]["preco"], "399.00")
        self.assertNotIn("retroatividade", por_codigo["E26MC3-PLFM"]["nome"])
        self.assertIn("retroatividade", por_codigo["K26MC5-1FM"]["nome"])
        self.assertEqual(por_codigo["G26OC5-D1FM"]["preco"], "257.25")

    def test_codigo_longo_vira_codigo_curto_e_o_nome_da_proposta_nao_repete_a_prestadora(self):
        self.assertEqual(encurtar_codigo_anadem("GRN26-DEM-BOL-100-COM-PF-4P"), "G26DB1-COMF4")
        self.assertEqual(encurtar_codigo_anadem("BLU26-MED-CC-300-1-PF-MEN"), "B26MC3-1FM")
        self.assertIsNone(encurtar_codigo_anadem("LAU-BAS-M"))
        self.assertEqual(
            nome_item_documento(
                "ANADEM GREEN 2026 — Medicina — Grupo 2 — Mensalidade",
                "ANADEM",
            ),
            "GREEN 2026 — Medicina — Grupo 2 — Mensalidade",
        )

    def test_linha_codigo_nome_preco_vira_servico_na_secao(self):
        itens = _parse_catalogo_pipe(
            [
                "ULTRASIS LAUDOS - MENSAL",
                "LAU-BAS-M | ULTRASIS LAUDOS Básico - mensal | R$ 63,00",
                "SERVIÇOS E ADICIONAIS",
                "ADESAO | Adesão única | R$ 375,00",
            ]
        )
        por_codigo = {item["codigo"]: item for item in itens}
        self.assertEqual(por_codigo["LAU-BAS-M"]["preco"], "63.00")
        self.assertEqual(por_codigo["LAU-BAS-M"]["recorrencia"], "mensal")
        self.assertEqual(pastas_do_item(por_codigo["LAU-BAS-M"]), ["ULTRASIS LAUDOS", "MENSAL"])
        self.assertEqual(pastas_do_item(por_codigo["ADESAO"]), ["SERVICOS E ADICIONAIS"])
        self.assertEqual(
            pasta_do_produto(
                "ANADEM GREEN 2026 — Medicina — Grupo 4 — Mensalidade — Boleto bancário",
                "G26MB10-4FM",
            ),
            "GRUPO 4",
        )
        self.assertEqual(pasta_do_produto("Plano essencial", "E26MC3-PLFM"), "")
        self.assertEqual(
            pasta_do_produto("ANADEM — Odontologia — Grupo D2 — Mensalidade", ""),
            "GRUPO D2",
        )
        self.assertEqual(
            pastas_do_item({"tabela": "GREEN", "area": "ODONTOLOGIA", "grupo": "D1", "pagamento": "BOL"}),
            ["ODONTOLOGIA", "TABELA GREEN", "GRUPO D1", "BOLETO BANCÁRIO"],
        )
        self.assertEqual(
            pasta_do_pagamento(
                "ANADEM GREEN 2026 — Medicina — Grupo 2 — 4 parcelas — Boleto bancário — capital 1.000.000,00",
                "G26MB10-2F4",
            ),
            "BOLETO BANCÁRIO",
        )
        self.assertEqual(
            pastas_do_item({"tabela": "ESSENCIAL", "area": "MEDICINA", "grupo": "PL"}),
            ["MEDICINA", "TABELA ESSENCIAL"],
        )
        self.assertEqual(por_codigo["ADESAO"]["preco"], "375.00")
        self.assertEqual(por_codigo["ADESAO"]["recorrencia"], "unico")

    def test_pdf_ultrasis_quando_o_arquivo_esta_disponivel(self):
        if not _PDF_ULTRASIS.is_file():
            self.skipTest("PDF da Ultrasys não está nesta máquina.")
        resultado = preview_catalogo_pdf(_PDF_ULTRASIS.read_bytes())
        por_codigo = {item["codigo"]: item for item in resultado["itens"]}
        self.assertGreaterEqual(resultado["total"], 20)
        self.assertEqual(por_codigo["LAU-BAS-M"]["preco"], "63.00")
        self.assertEqual(por_codigo["LAU-INT-A"]["preco"], "1095.00")
        self.assertEqual(por_codigo["ADESAO"]["preco"], "375.00")
