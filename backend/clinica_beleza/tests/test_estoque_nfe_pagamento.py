"""Pagamento da NF-e: à vista, vencimento ou pergunta depois."""
from datetime import date
from decimal import Decimal
from unittest import TestCase
from xml.etree import ElementTree as ET

from clinica_beleza.estoque_nfe_pagamento import (
    _data_texto,
    descricao_da_compra,
    descricao_sem_nota,
    montar_lancamentos,
    pagamento_da_nfe,
)

NS = "http://www.portalfiscal.inf.br/nfe"


def _nfe(miolo: str):
    return ET.fromstring(
        f'<infNFe xmlns="{NS}">{miolo}</infNFe>',
    )


class PagamentoNfeTests(TestCase):
    def test_duplicata_fica_pendente(self):
        pagamento = pagamento_da_nfe(
            _nfe(
                "<cobr><dup><nDup>001</nDup><dVenc>2026-12-10</dVenc><vDup>378.00</vDup></dup></cobr>"
                "<pag><detPag><indPag>1</indPag><tPag>15</tPag><vPag>378.00</vPag></detPag></pag>",
            ),
            data_emissao="2026-11-09",
            valor_total="378.00",
        )
        self.assertEqual(pagamento["situacao"], "pendente")
        self.assertEqual(pagamento["parcelas"][0]["vencimento"], "2026-12-10")
        lancamentos = montar_lancamentos(
            pagamento, numero="470044", fornecedor="VICTALAB", chave="1" * 44,
        )
        self.assertEqual(lancamentos[0]["status"], "PENDING")
        self.assertEqual(lancamentos[0]["data_vencimento"], "2026-12-10")
        self.assertEqual(lancamentos[0]["valor"], Decimal("378.00"))
        self.assertEqual(lancamentos[0]["numero_nota"], "470044")
        self.assertEqual(lancamentos[0]["fornecedor_nome"], "VICTALAB")

    def test_a_vista_fica_paga(self):
        pagamento = pagamento_da_nfe(
            _nfe("<pag><detPag><indPag>0</indPag><tPag>17</tPag><vPag>189.00</vPag></detPag></pag>"),
            data_emissao="2026-11-09",
            valor_total="189.00",
        )
        self.assertEqual(pagamento["situacao"], "pago")
        self.assertEqual(pagamento["forma_pagamento"], "PIX")
        lancamentos = montar_lancamentos(
            pagamento, numero="12", fornecedor="LAB", chave="", hoje=date(2026, 11, 9),
        )
        self.assertEqual(lancamentos[0]["status"], "PAID")
        self.assertEqual(lancamentos[0]["data_pagamento"], "2026-11-09")

    def test_sem_pagamento_nao_lanca_ate_a_resposta(self):
        pagamento = pagamento_da_nfe(_nfe("<total></total>"), valor_total="50.00")
        self.assertEqual(pagamento["situacao"], "indefinido")
        self.assertEqual(
            montar_lancamentos(pagamento, numero="1", fornecedor="X", chave=""),
            [],
        )
        pendente = montar_lancamentos(
            pagamento, numero="1", fornecedor="X", chave="", pago=False, data_vencimento="2026-12-01",
        )
        self.assertEqual(pendente[0]["status"], "PENDING")
        self.assertEqual(pendente[0]["data_vencimento"], "2026-12-01")
        pago = montar_lancamentos(
            pagamento, numero="1", fornecedor="X", chave="", pago=True, hoje=date(2026, 11, 11),
        )
        self.assertEqual(pago[0]["status"], "PAID")

    def test_data_em_texto_nao_quebra_a_resposta(self):
        self.assertEqual(_data_texto("2026-11-09"), "2026-11-09")
        self.assertEqual(_data_texto(date(2026, 11, 9)), "2026-11-09")

    def test_descricao_e_o_produto_nao_a_nota(self):
        self.assertEqual(descricao_da_compra(["VITAMINA D3"]), "VITAMINA D3")
        self.assertEqual(
            descricao_sem_nota(
                "NF 63028 — NEXTPHARMA Farmacia de Manipulacao Ltda",
                "63028",
                "NEXTPHARMA Farmacia de Manipulacao Ltda",
            ),
            "",
        )
        pagamento = pagamento_da_nfe(
            _nfe("<pag><detPag><indPag>0</indPag><tPag>01</tPag><vPag>378.00</vPag></detPag></pag>"),
            data_emissao="2026-11-09",
            valor_total="378.00",
        )
        lancamento = montar_lancamentos(
            pagamento,
            numero="63028",
            fornecedor="NEXTPHARMA",
            chave="",
            nomes=["VITAMINA D3 (CX COM 10 AMPOLAS 2ML)"],
        )[0]
        self.assertEqual(lancamento["descricao"], "VITAMINA D3 (CX COM 10 AMPOLAS 2ML)")
        self.assertEqual(lancamento["numero_nota"], "63028")
