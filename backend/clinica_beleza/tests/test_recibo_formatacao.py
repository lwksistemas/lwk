"""Testes unitários do recibo (rótulo CPF/CNPJ, telefone, desconto em notes)."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.recibo.context import desconto_concedido
from clinica_beleza.recibo_service import (
    _extrair_desconto_notes,
    _label_documento_loja,
    _linha_documento_loja,
)


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
        self.assertEqual(ctx["abatimento_label"], "Abatimento — Bioestimulador de Colágeno")
        linhas = _linhas_descontos_recibo(ctx)
        self.assertNotIn(("Desconto retorno", 150), linhas)
        self.assertIn((ctx["abatimento_label"], ctx["abatimento"]), linhas)
        soma_descontos = sum(valor for _label, valor in linhas)
        self.assertEqual(round(ctx["subtotal"] - soma_descontos, 2), 610)

    def test_linha_zerada_usa_preco_de_cadastro_que_fecha_a_conta(self):
        from clinica_beleza.recibo.context import reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": True,
            "taxa_consulta": 0,
            "taxa_consulta_referencia": 150,
            "desconto_retorno": 150,
            "desconto": 80,
            "procedimentos": [{"nome": "LASER ETHEREA", "valor": 0, "preco_cadastro": 380}],
            "subtotal": 150,
            "valor_total": 300,
            "valor_pago": 300,
            "saldo_devedor": 0,
        })
        self.assertEqual(ctx["procedimentos"][0]["valor"], 380)
        self.assertEqual(ctx["subtotal"], 380)
        self.assertEqual(ctx["desconto_retorno"], 0)
        self.assertEqual(ctx["valor_total"], 300)
        self.assertNotIn("abatimento", ctx)

    def test_desconto_comercial_sai_do_total(self):
        from clinica_beleza.recibo.context import reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": False,
            "taxa_consulta": 0,
            "desconto": 500,
            "procedimentos": [{"nome": "PROCEDIMENTO", "valor": 1500}],
            "subtotal": 1500,
            "valor_total": 1500,
            "valor_pago": 0,
            "saldo_devedor": 1500,
        })
        self.assertEqual(ctx["valor_total"], 1000)
        self.assertEqual(ctx["saldo_devedor"], 1000)
        self.assertNotIn("abatimento", ctx)

    def test_desconto_do_produto_sobe_o_subtotal_para_o_preco_cheio(self):
        from clinica_beleza.recibo.context import _linhas_descontos_recibo, reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "somente_produtos": True,
            "retorno_gratuito": False,
            "taxa_consulta": 0,
            "desconto": 0,
            "procedimentos": [],
            "produtos": [{
                "nome": "BELOTERO INTENSE LIDOCAINA FR 1ML MERZ",
                "quantidade": "1",
                "preco_unitario": 300,
                "desconto": 35,
                "subtotal": 265,
            }],
            "subtotal": 265,
            "valor_total": 265,
            "valor_pago": 265,
            "saldo_devedor": 0,
        })
        self.assertEqual(ctx["subtotal"], 300)
        self.assertEqual(ctx["desconto"], 35)
        self.assertEqual(ctx["valor_total"], 265)
        self.assertNotIn("abatimento", ctx)
        self.assertEqual(_linhas_descontos_recibo(ctx), [("Desconto", 35)])

    def test_desconto_ja_liquido_nao_sai_de_novo(self):
        from clinica_beleza.recibo.context import reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": False,
            "taxa_consulta": 0,
            "desconto": 500,
            "procedimentos": [{"nome": "PROCEDIMENTO", "valor": 1500}],
            "subtotal": 1500,
            "valor_total": 1000,
            "valor_pago": 0,
            "saldo_devedor": 1000,
        })
        self.assertEqual(ctx["valor_total"], 1000)
        self.assertEqual(ctx["saldo_devedor"], 1000)

    def test_retorno_e_desconto_comercial_fecham_o_saldo(self):
        from clinica_beleza.recibo.context import reconciliar_conta_recibo

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": True,
            "taxa_consulta": 0,
            "taxa_consulta_referencia": 150,
            "desconto_retorno": 150,
            "desconto": 200,
            "procedimentos": [{"nome": "BOTOX", "valor": 1500}],
            "subtotal": 1650,
            "valor_total": 1500,
            "valor_pago": 0,
            "saldo_devedor": 1500,
        })
        self.assertEqual(ctx["valor_total"], 1300)
        self.assertEqual(ctx["saldo_devedor"], 1300)

    def test_consulta_nao_lancada_nao_afirma_desconto(self):
        from clinica_beleza.recibo.context import (
            _linhas_descontos_recibo,
            _linhas_taxa_consulta_recibo,
            nome_exibicao_procedimento_recibo,
            reconciliar_conta_recibo,
        )

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": True,
            "taxa_consulta": 0,
            "taxa_consulta_referencia": 150,
            "desconto_retorno": 150,
            "desconto": 0,
            "procedimentos": [{"nome": "PREENCHIMENTO DE GLÚTEOS 100 ML", "valor": 6000}],
            "subtotal": 6150,
            "valor_total": 6000,
            "valor_pago": 650,
            "saldo_devedor": 5350,
            "retorno_aviso": "Retorno gratuito em até 30 dias após o atendimento.",
        })
        self.assertEqual(ctx["valor_total"], 6000)
        self.assertEqual(ctx["saldo_devedor"], 5350)
        self.assertEqual(_linhas_taxa_consulta_recibo(ctx), [])
        self.assertEqual(_linhas_descontos_recibo(ctx), [])
        self.assertEqual(
            nome_exibicao_procedimento_recibo(ctx["procedimentos"][0]["nome"]),
            "Preenchimento de Glúteos — 100 mL",
        )
        self.assertNotIn("descontada", ctx["retorno_aviso"])

    def test_descricao_fica_com_a_primeira_letra_maiuscula(self):
        from clinica_beleza.recibo.context import (
            nome_exibicao_procedimento_recibo,
            produtos_exibidos_recibo,
        )

        self.assertEqual(
            nome_exibicao_procedimento_recibo("LIMPEZA DE PELE PROFUNDA"),
            "Limpeza de Pele Profunda",
        )
        self.assertEqual(
            nome_exibicao_procedimento_recibo("PEELING QUÍMICO FACIAL"),
            "Peeling Químico Facial",
        )
        self.assertEqual(
            nome_exibicao_procedimento_recibo("Limpeza de Pele Profunda"),
            "Limpeza de Pele Profunda",
        )
        linhas = produtos_exibidos_recibo({
            "produtos": [{
                "nome": "PROTETOR SOLAR FPS 50",
                "quantidade": "1",
                "preco_unitario": 80,
                "desconto": 0,
                "subtotal": 80,
            }],
        })
        self.assertEqual(linhas[0]["nome"], "Protetor Solar FPS 50")

    def test_consulta_lancada_e_descontada_mostra_a_conta(self):
        from clinica_beleza.recibo.context import (
            _linhas_descontos_recibo,
            _linhas_taxa_consulta_recibo,
            reconciliar_conta_recibo,
        )

        ctx = reconciliar_conta_recibo({
            "retorno_gratuito": True,
            "taxa_consulta": 150,
            "taxa_consulta_referencia": 150,
            "desconto_retorno": 150,
            "desconto": 0,
            "procedimentos": [{"nome": "PREENCHIMENTO DE GLÚTEOS 100 ML", "valor": 6000}],
            "subtotal": 6150,
            "valor_total": 6150,
            "valor_pago": 650,
            "saldo_devedor": 5500,
        })
        self.assertEqual(
            _linhas_taxa_consulta_recibo(ctx),
            [("Taxa de avaliação", 150.0)],
        )
        self.assertEqual(
            _linhas_descontos_recibo(ctx),
            [("Desconto da avaliação", 150.0)],
        )
        self.assertEqual(ctx["subtotal"], 6150)
        self.assertEqual(ctx["valor_total"], 6000)
        self.assertEqual(ctx["saldo_devedor"], 5350)

    def test_vencido_quando_a_data_passou_e_parcial_lista_os_recebimentos(self):
        from clinica_beleza.recibo.context import (
            formas_detalhadas_recibo,
            linha_vencimento_recibo,
        )

        self.assertEqual(
            linha_vencimento_recibo({
                "vencimento": "12/10/2026",
                "data_emissao": "04/11/2026 12:06",
            }),
            "Vencido em: 12/10/2026",
        )
        self.assertEqual(
            linha_vencimento_recibo({
                "vencimento": "20/11/2026",
                "data_emissao": "04/11/2026 12:06",
            }),
            "Vencimento: 20/11/2026",
        )
        self.assertEqual(linha_vencimento_recibo({"vencimento": ""}), "Sem vencimento")
        linhas = formas_detalhadas_recibo({
            "formas_pagamento": [
                {"metodo": "Cartão de Débito (30/09/2026)", "valor": 650},
                {"metodo": "Cartão de Débito (07/10/2026)", "valor": 400},
            ],
        })
        self.assertEqual(linhas, [
            {"data": "30/09/2026", "forma": "Cartão de Débito", "valor": 650.0},
            {"data": "07/10/2026", "forma": "Cartão de Débito", "valor": 400.0},
        ])

    def test_recebido_a_maior(self):
        from clinica_beleza.recibo.context import recebido_a_maior_recibo

        self.assertEqual(recebido_a_maior_recibo({"valor_total": 1900, "valor_pago": 2300}), 400)
        self.assertEqual(recebido_a_maior_recibo({"valor_total": 300, "valor_pago": 300}), 0)
