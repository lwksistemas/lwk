"""Reconhecimento de item da NF-e: código do fornecedor, GTIN, nome e caixa."""
from decimal import Decimal
from unittest import TestCase

from clinica_beleza.estoque_lotes import consumir_lotes, resumo_saldos, saldo_utilizavel
from clinica_beleza.estoque_nfe_vinculo import (
    chave_item_identico,
    classificar_item,
    custo_comercial_efetivo,
    custo_total_estoque,
    custo_unitario_estoque,
    decisao_pendente,
    embalagem_na_descricao,
    fator_da_unidade,
    gtin_util,
    marcar_repetidos,
    quantidade_estoque,
    rastreio_obrigatorio_faltando,
    serie_da_chave,
)
from clinica_beleza.estoque_xml_import_service import nome_do_cadastro, parse_nfe_xml

XML_CAIXA = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe><infNFe Id="NFe35260104252011000110550010000000011000000010">
    <ide><nNF>11</nNF><dhEmi>2026-11-03T10:00:00-03:00</dhEmi></ide>
    <emit><CNPJ>04252011000110</CNPJ><xNome>FORNECEDOR</xNome></emit>
    <dest><CNPJ>37302743000126</CNPJ><xNome>HARMONIS</xNome></dest>
    <det nItem="1"><prod>
      <cProd>AH-01</cProd><cEAN>7891234567895</cEAN>
      <xProd>ACIDO HIALURONICO</xProd><NCM>30049099</NCM>
      <uCom>CX</uCom><qCom>2.0000</qCom><vUnCom>100.00</vUnCom><vProd>200.00</vProd>
      <cEANTrib>7891234567895</cEANTrib><uTrib>UN</uTrib><qTrib>10.0000</qTrib><vUnTrib>20.00</vUnTrib>
    </prod><rastro><nLote>L1</nLote><dVal>2027-01-01</dVal></rastro></det>
  </infNFe></NFe>
</nfeProc>
""".encode()


class FatorUnidadeTests(TestCase):
    def test_caixa_com_cinco_frascos(self):
        fator = fator_da_unidade(Decimal("2"), Decimal("10"), "CX", "UN")
        self.assertEqual(fator, Decimal("5.0000"))
        self.assertEqual(quantidade_estoque(Decimal("2"), fator), Decimal("10.00"))

    def test_mesma_unidade_nao_converte(self):
        self.assertEqual(fator_da_unidade(Decimal("2"), Decimal("2"), "UN", "UN"), Decimal("1"))

    def test_caixa_escrita_no_nome_vira_ampola(self):
        achado = embalagem_na_descricao("VITAMINA D3 (CX COM 10 AMPOLAS 2ML)")
        self.assertEqual(achado["quantidade"], Decimal("10"))
        self.assertEqual(achado["unidade"], "ampola")
        self.assertIsNone(embalagem_na_descricao("SORO FISIOLOGICO 2ML"))

    def test_gtin_vazio_da_nota(self):
        self.assertEqual(gtin_util("SEM GTIN"), "")
        self.assertEqual(gtin_util("00000000"), "")
        self.assertEqual(gtin_util("7891234567895"), "7891234567895")


class ClassificarItemTests(TestCase):
    def test_codigo_do_fornecedor_vincula_sem_perguntar(self):
        produtos = [{"id": 7, "nome": "ÁCIDO HIALURÔNICO"}]
        vinculos = [{"produto_id": 7, "documento": "04252011000110", "codigo": "AH-01", "gtin": "", "fator": "5"}]
        item = classificar_item(
            {"nome": "ACIDO HIALURONICO 1ML", "codigo": "AH-01", "gtin": "", "documento": "04.252.011/0001-10", "fator": Decimal("1")},
            produtos,
            vinculos,
        )
        self.assertEqual(item["acao"], "vincular")
        self.assertEqual(item["confianca"], "alta")
        self.assertEqual(item["produto_id"], 7)
        self.assertEqual(item["fator"], "5")

    def test_gtin_de_outro_fornecedor_acha_o_mesmo_produto(self):
        produtos = [{"id": 7, "nome": "ÁCIDO HIALURÔNICO"}]
        vinculos = [{"produto_id": 7, "documento": "111", "codigo": "X", "gtin": "7891234567895", "fator": "1"}]
        item = classificar_item(
            {"nome": "AH OUTRA MARCA", "codigo": "ZZ", "gtin": "7891234567895", "documento": "222", "fator": Decimal("1")},
            produtos,
            vinculos,
        )
        self.assertEqual(item["acao"], "vincular")
        self.assertEqual(item["produto_id"], 7)

    def test_nome_parecido_pede_confirmacao(self):
        produtos = [{"id": 3, "nome": "ACIDO HIALURONICO"}]
        item = classificar_item(
            {"nome": "ACIDO HIALURONICO 1ML", "codigo": "NOVO", "gtin": "", "documento": "222", "fator": Decimal("1")},
            produtos,
            [],
        )
        self.assertEqual(item["acao"], "")
        self.assertEqual(item["confianca"], "duvida")
        self.assertEqual(item["produto_id"], 3)

    def test_sem_correspondencia_cadastra(self):
        item = classificar_item(
            {"nome": "SERINGA DESCARTAVEL", "codigo": "S1", "gtin": "", "documento": "222", "fator": Decimal("1")},
            [{"id": 1, "nome": "BOTOX"}],
            [],
        )
        self.assertEqual(item["acao"], "novo")


class CustoEIdentidadeTests(TestCase):
    def test_caixa_de_262_vira_52_40_por_frasco(self):
        comercial = custo_comercial_efetivo(Decimal("262"), Decimal("2"), Decimal("524"))
        fator = fator_da_unidade(Decimal("2"), Decimal("10"), "CX", "UN")
        self.assertEqual(custo_unitario_estoque(comercial, fator), Decimal("52.40"))
        self.assertEqual(quantidade_estoque(Decimal("2"), fator), Decimal("10.00"))

    def test_desconto_e_frete_entram_no_custo(self):
        comercial = custo_comercial_efetivo(
            Decimal("100"), Decimal("2"), Decimal("200"), Decimal("20"), Decimal("10"), Decimal("0"), Decimal("4"),
        )
        self.assertEqual(comercial, Decimal("97.0000"))
        self.assertEqual(custo_unitario_estoque(comercial, Decimal("1")), Decimal("97.00"))

    def test_quilo_nao_vira_unidade(self):
        fator = fator_da_unidade(Decimal("0.2000"), Decimal("0.2000"), "KG", "KG")
        self.assertEqual(fator, Decimal("1"))
        self.assertEqual(custo_unitario_estoque(Decimal("10.00"), fator), Decimal("10.00"))

    def test_codigo_e_gtin_conflitantes_pedem_escolha(self):
        produtos = [{"id": 1, "nome": "A"}, {"id": 2, "nome": "B"}]
        vinculos = [
            {"produto_id": 1, "documento": "111", "codigo": "C1", "gtin": "", "fator": "1"},
            {"produto_id": 2, "documento": "222", "codigo": "C2", "gtin": "7891234567895", "fator": "1"},
        ]
        item = classificar_item(
            {"nome": "ITEM", "codigo": "C1", "gtin": "7891234567895", "documento": "111", "fator": Decimal("1")},
            produtos,
            vinculos,
        )
        self.assertEqual(item["acao"], "")
        self.assertEqual({c["id"] for c in item["candidatos"]}, {1, 2})

    def test_nome_parecido_nao_e_o_mesmo_item(self):
        a = chave_item_identico({"nome": "ACIDO HIALURONICO", "gtin": ""})
        b = chave_item_identico({"nome": "ACIDO HIALURONICO 1ML", "gtin": ""})
        self.assertNotEqual(a, b)
        mesmo = chave_item_identico({"nome": "OUTRO NOME", "gtin": "7891234567895"})
        igual = chave_item_identico({"nome": "NOME DIFERENTE", "gtin": "7891234567895"})
        self.assertEqual(mesmo, igual)

    def test_gtins_diferentes_nao_repetem_juntos(self):
        itens = [
            {"nome": "AGULHA", "gtin": "7891234567895", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
            {"nome": "AGULHA", "gtin": "7891234567896", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
        ]
        marcar_repetidos(itens)
        self.assertEqual(itens[0]["acao"], "novo")
        self.assertNotEqual(itens[0]["grupo"], itens[1]["grupo"])

    def test_exige_lote_sem_validade_bloqueia(self):
        self.assertTrue(rastreio_obrigatorio_faltando(True, "vincular", "L1", None))
        self.assertFalse(rastreio_obrigatorio_faltando(True, "ignorar", "", None))
        self.assertFalse(rastreio_obrigatorio_faltando(False, "vincular", "", None))

    def test_saida_consome_o_lote_que_vence_antes(self):
        from datetime import date

        hoje = date(2026, 11, 3)
        lotes = consumir_lotes(
            [
                {"id": 1, "quantidade": Decimal("4"), "validade": date(2027, 6, 1)},
                {"id": 2, "quantidade": Decimal("6"), "validade": date(2027, 1, 1)},
            ],
            Decimal("5"),
            hoje,
        )
        por_id = {lote["id"]: lote["quantidade"] for lote in lotes}
        self.assertEqual(por_id[2], Decimal("1"))
        self.assertEqual(por_id[1], Decimal("4"))

    def test_saldo_antigo_fica_fora_dos_lotes_depois_da_saida(self):
        from datetime import date

        hoje = date(2026, 11, 3)
        quantidade = Decimal("15")
        lotes = []
        quantidade += Decimal("5")
        lotes.append({"id": 1, "codigo": "A", "quantidade": Decimal("5"), "validade": date(2027, 1, 1)})
        quantidade += Decimal("8")
        lotes.append({"id": 2, "codigo": "B", "quantidade": Decimal("8"), "validade": date(2027, 6, 1)})
        self.assertEqual(quantidade - sum(lote["quantidade"] for lote in lotes), Decimal("15"))
        quantidade -= Decimal("3")
        lotes = consumir_lotes(lotes, Decimal("3"), hoje)
        por_id = {lote["id"]: lote["quantidade"] for lote in lotes}
        self.assertEqual(por_id[1], Decimal("2"))
        self.assertEqual(por_id[2], Decimal("8"))
        self.assertEqual(quantidade - sum(por_id.values()), Decimal("15"))

    def test_quando_os_lotes_novos_acabam_o_saldo_antigo_continua_utilizavel(self):
        from datetime import date

        hoje = date(2026, 11, 3)
        quantidade = Decimal("15")
        lotes = [
            {"id": 1, "quantidade": Decimal("5"), "validade": date(2027, 1, 1)},
            {"id": 2, "quantidade": Decimal("8"), "validade": date(2027, 6, 1)},
            {"id": 3, "quantidade": Decimal("4"), "validade": date(2026, 1, 1)},
        ]
        quantidade += Decimal("17")
        antes = resumo_saldos(quantidade, lotes, hoje=hoje)
        self.assertEqual(antes["total"], Decimal("32"))
        self.assertEqual(antes["utilizavel"], Decimal("28"))
        self.assertEqual(antes["sem_lote"], Decimal("15"))

        quantidade -= Decimal("13")
        lotes = [lote for lote in consumir_lotes(lotes, Decimal("13"), hoje) if lote["quantidade"] > 0]
        no_fim_dos_novos = resumo_saldos(quantidade, lotes, hoje=hoje)
        self.assertEqual(no_fim_dos_novos["em_lotes"], Decimal("4"))
        self.assertEqual(no_fim_dos_novos["sem_lote"], Decimal("15"))
        self.assertEqual(no_fim_dos_novos["total"], Decimal("19"))
        self.assertEqual(no_fim_dos_novos["utilizavel"], Decimal("15"))

        quantidade -= Decimal("6")
        lotes = [lote for lote in consumir_lotes(lotes, Decimal("6"), hoje) if lote["quantidade"] > 0]
        depois = resumo_saldos(quantidade, lotes, hoje=hoje)
        self.assertEqual(depois["total"], Decimal("13"))
        self.assertEqual(depois["sem_lote"], Decimal("9"))
        self.assertEqual(depois["utilizavel"], Decimal("9"))
        self.assertEqual(depois["em_lotes"], Decimal("4"))

    def test_vencido_e_sem_validade_nao_furam_a_fila(self):
        from datetime import date

        hoje = date(2026, 11, 3)
        lotes = consumir_lotes(
            [
                {"id": 1, "quantidade": Decimal("5"), "validade": date(2026, 1, 1)},
                {"id": 2, "quantidade": Decimal("8"), "validade": date(2027, 1, 1)},
                {"id": 3, "quantidade": Decimal("4"), "validade": None},
            ],
            Decimal("9"),
            hoje,
        )
        por_id = {lote["id"]: lote["quantidade"] for lote in lotes}
        self.assertEqual(por_id[1], Decimal("5"))
        self.assertEqual(por_id[2], Decimal("0"))
        self.assertEqual(por_id[3], Decimal("3"))
        self.assertEqual(
            saldo_utilizavel(Decimal("8"), [{"quantidade": Decimal("8"), "validade": date(2020, 1, 1)}], hoje=hoje),
            Decimal("0"),
        )
        self.assertEqual(
            saldo_utilizavel(Decimal("10"), [], ativo=False, hoje=hoje),
            Decimal("0"),
        )

    def test_tres_fornecedores_um_produto_pelo_gtin(self):
        produto = {"id": 7, "nome": "ACIDO HIALURONICO"}
        vinculos = [{"produto_id": 7, "documento": "111", "codigo": "A", "gtin": "7891234567895", "fator": "5"}]
        for doc, codigo, nome in (
            ("111", "A", "ACIDO HIALURONICO"),
            ("222", "B-99", "AH FRASCO 1ML"),
            ("333", "C-7", "PREENCHEDOR FACIAL"),
        ):
            item = classificar_item(
                {"nome": nome, "codigo": codigo, "gtin": "7891234567895", "documento": doc, "fator": Decimal("5")},
                [produto],
                vinculos,
            )
            self.assertEqual(item["produto_id"], 7)
            self.assertEqual(item["acao"], "vincular")

    def test_linhas_iguais_guardam_lotes_diferentes(self):
        itens = [
            {"nome": "AGULHA", "gtin": "7891234567895", "lote": "A", "validade": "2027-01-01", "quantidade": "5", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
            {"nome": "AGULHA 30G", "gtin": "7891234567895", "lote": "B", "validade": "2028-06-01", "quantidade": "8", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
        ]
        marcar_repetidos(itens)
        self.assertEqual(itens[0]["grupo"], itens[1]["grupo"])
        self.assertEqual(itens[0]["lote"], "A")
        self.assertEqual(itens[1]["lote"], "B")
        self.assertEqual(itens[0]["quantidade"], "5")
        self.assertEqual(itens[1]["quantidade"], "8")
        self.assertEqual(itens[0]["acao"], "")

    def test_serie_e_total_da_caixa(self):
        comercial = custo_comercial_efetivo(Decimal("262"), Decimal("2"), Decimal("524"))
        fator = fator_da_unidade(Decimal("2"), Decimal("10"), "CX", "UN")
        unitario = custo_unitario_estoque(comercial, fator)
        self.assertEqual(custo_total_estoque(unitario, Decimal("10")), Decimal("524.00"))
        self.assertEqual(serie_da_chave("35260104252011000110550010000000011000000010"), "1")

    def test_decisao_pendente_nao_libera_a_nota(self):
        self.assertTrue(decisao_pendente("", None))
        self.assertTrue(decisao_pendente("vincular", None))
        self.assertFalse(decisao_pendente("novo", None))
        self.assertFalse(decisao_pendente("ignorar", None))

    def test_nome_comercial_entra_no_estoque(self):
        self.assertEqual(
            nome_do_cadastro({"nome": "TOXINA BOTULINICA", "nome_comercial": "Botox"}),
            "Botox",
        )
        self.assertEqual(nome_do_cadastro({"nome": "TOXINA BOTULINICA", "nome_comercial": "  "}), "TOXINA BOTULINICA")

    def test_confirmacao_esta_dentro_de_uma_transacao(self):
        import inspect

        from clinica_beleza.estoque_xml_import_service import confirmar_importacao_xml

        texto = inspect.getsource(confirmar_importacao_xml)
        self.assertIn("transaction.atomic", texto)
        self.assertIn("decisao_pendente", texto)


class RepetidosEXmlTests(TestCase):
    def test_repetido_na_nota_nao_cadastra_calado(self):
        itens = [
            {"nome": "AGULHA", "gtin": "", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
            {"nome": "AGULHA", "gtin": "", "acao": "novo", "confianca": "nenhuma", "alerta": ""},
        ]
        marcar_repetidos(itens)
        self.assertEqual(itens[0]["acao"], "")
        self.assertIn("repete", itens[1]["alerta"])

    def test_xml_le_gtin_fator_e_lote(self):
        parsed = parse_nfe_xml(XML_CAIXA)
        item = parsed["produtos"][0]
        self.assertEqual(item["gtin"], "7891234567895")
        self.assertEqual(item["codigo_produto"], "AH-01")
        self.assertEqual(Decimal(item["fator"]), Decimal("5.0000"))
        self.assertEqual(item["lote"], "L1")
        self.assertEqual(item["validade"], "2027-01-01")
        self.assertEqual(parsed["chave"], "35260104252011000110550010000000011000000010")
