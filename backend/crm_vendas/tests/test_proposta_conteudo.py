"""A descrição do serviço escolhido entra no conteúdo da proposta."""
from django.test import SimpleTestCase

from crm_vendas.pdf_proposta_contrato.formatters import conteudo_com_descricoes


class _Produto:
    def __init__(self, descricao):
        self.descricao = descricao


class _Item:
    def __init__(self, descricao):
        self.produto_servico = _Produto(descricao)


class _Itens:
    def __init__(self, itens):
        self._itens = itens

    def select_related(self, *_args):
        return self

    def all(self):
        return self._itens


class _Oportunidade:
    def __init__(self, descricoes):
        self.itens = _Itens([_Item(texto) for texto in descricoes])


class ConteudoPropostaTests(SimpleTestCase):
    def test_descricao_do_servico_entra_no_conteudo(self):
        descricao = (
            "ANADEM GREEN 2026. Medicina. Pessoa física. 4 parcelas. "
            "Especialidades: ACUPUNTURA, ALERGIA E IMUNOLOGIA."
        )
        texto = conteudo_com_descricoes("Condições gerais.", _Oportunidade([descricao]))
        self.assertIn("Condições gerais.", texto)
        self.assertIn("ACUPUNTURA, ALERGIA E IMUNOLOGIA.", texto)

    def test_nao_repete_descricao_ja_gravada(self):
        descricao = "ANADEM GREEN 2026. Medicina. Pessoa física."
        self.assertEqual(
            conteudo_com_descricoes(descricao, _Oportunidade([descricao])),
            descricao,
        )

    def test_rotulo_curto_do_plano_sai_do_conteudo(self):
        base = "Prazo de Liberação: acesso em até 24 horas."
        texto = conteudo_com_descricoes(
            f"{base}\n\nUltrasis Laudos - Mensal",
            _Oportunidade(["Ultrasis Laudos - Mensal"]),
        )
        self.assertEqual(texto, base)
        self.assertNotIn("Ultrasis Laudos - Mensal", texto)

    def test_resumo_separa_pagamento_inicial_e_mensalidade(self):
        from crm_vendas.pdf_proposta_contrato.formatters import linhas_resumo_investimento

        linhas, frase = linhas_resumo_investimento(unico=750, mensal=392, valor_total=1142)
        self.assertEqual(linhas[0], ("Pagamento inicial:", "R$ 1.142,00"))
        self.assertIn(("Mensalidades seguintes:", "R$ 392,00/mês"), linhas)
        self.assertIn("R$ 750,00 de implantação", frase)
        self.assertIn("R$ 392,00 da primeira mensalidade", frase)
        self.assertIn("cobradas uma única vez", frase)

    def test_resumo_visual_coloca_a_frase_entre_os_valores(self):
        from crm_vendas.pdf_proposta_contrato.formatters import texto_resumo_visual

        linhas = [
            ("Pagamento inicial:", "R$ 1.142,00"),
            ("Mensalidades seguintes:", "R$ 392,00/mês"),
        ]
        frase = (
            "Inclui R$ 750,00 de implantação + R$ 392,00 da primeira mensalidade. "
            "As taxas de implantação são cobradas uma única vez."
        )
        blocos = texto_resumo_visual(linhas, frase)
        self.assertEqual(
            [texto for texto, _negrito in blocos],
            [
                "Pagamento inicial: R$ 1.142,00",
                "Inclui R$ 750,00 de implantação + R$ 392,00 da primeira mensalidade.",
                "Mensalidades seguintes: R$ 392,00/mês.",
                "As taxas de implantação são cobradas uma única vez.",
            ],
        )
        self.assertEqual([negrito for _texto, negrito in blocos], [True, False, True, False])

    def test_banco_sai_do_template_para_a_primeira_folha(self):
        from crm_vendas.pdf_proposta_contrato.formatters import (
            extrair_pagamento_inicial,
            partir_condicoes,
            separar_subtitulo,
        )

        texto = [
            "Sistema de Laudos • Captura DICOM • Worklist",
            "Acesso às imagens: consulta por QR Code.",
            "Requisitos do aparelho",
            "O aparelho precisa da licença DICOM.",
            "Dados para o pagamento inicial",
            "Banco Itaú • Agência: 4864 • Conta: 17.777-1",
            "Beneficiário: Ultrasis Informática Ltda",
        ]
        subtitulo, resto = separar_subtitulo(texto)
        intro, secoes = partir_condicoes(resto)
        titulo, linhas, intro, secoes = extrair_pagamento_inicial(intro, secoes)
        self.assertEqual(subtitulo, "Sistema de Laudos • Captura DICOM • Worklist")
        self.assertEqual(titulo, "Dados para o pagamento inicial")
        self.assertEqual(linhas[0], "Banco Itaú • Agência: 4864 • Conta: 17.777-1")
        self.assertEqual(intro, ["Acesso às imagens: consulta por QR Code."])
        self.assertEqual([secao["titulo"] for secao in secoes], ["Requisitos do aparelho"])

    def test_editor_separa_a_primeira_folha_da_segunda(self):
        from crm_vendas.pdf_proposta_contrato.formatters import (
            dividir_folhas_marcadas,
            partir_condicoes,
            titulo_e_corpo_da_primeira_folha,
        )

        blocos = [
            "Dados para pagamento",
            "Banco, agência, conta, CNPJ e PIX da Anadem",
            "",
            "Linha curta",
            "[[folha:2]]",
            "Vantagens de ser um cliente Anadem",
            "Cobertura nacional.",
        ]
        primeira, seguintes = dividir_folhas_marcadas(blocos)
        titulo, linhas = titulo_e_corpo_da_primeira_folha(primeira)
        intro, secoes = partir_condicoes(seguintes)
        self.assertEqual(titulo, "Dados para pagamento")
        self.assertEqual(linhas[0], "Banco, agência, conta, CNPJ e PIX da Anadem")
        self.assertIn("Linha curta", linhas)
        self.assertEqual(intro, [])
        self.assertEqual(secoes[0]["titulo"], "Vantagens de ser um cliente Anadem")
        self.assertEqual(secoes[0]["paragrafos"], ["Cobertura nacional."])

    def test_template_padrao_manda_a_primeira_folha_para_o_pdf(self):
        from crm_vendas.pdf_proposta_contrato.formatters import (
            MARCA_SEGUNDA_FOLHA,
            dividir_folhas_marcadas,
            escolher_conteudo_narrativo,
            titulo_e_corpo_da_primeira_folha,
        )

        antigo = "Vantagens de ser um cliente Anadem\nTexto que já estava na proposta."
        template = "\n".join([
            "Banco, agência, conta, CNPJ e PIX da Anadem",
            "",
            "Tenha segurança e tranquilidade",
            MARCA_SEGUNDA_FOLHA,
            "Vantagens de ser um cliente Anadem",
        ])
        escolhido = escolher_conteudo_narrativo(antigo, template)
        primeira, _seguintes = dividir_folhas_marcadas(escolhido.split("\n"))
        titulo, linhas = titulo_e_corpo_da_primeira_folha(primeira)
        self.assertEqual(titulo, "Banco, agência, conta, CNPJ e PIX da Anadem")
        self.assertIn("Tenha segurança e tranquilidade", linhas)
        self.assertEqual(
            escolher_conteudo_narrativo(antigo, "Texto antigo do template, sem divisão."),
            antigo,
        )

    def test_condicoes_ficam_sem_a_descricao_do_servico(self):
        from crm_vendas.pdf_proposta_contrato.formatters import paragrafos_condicoes

        descricao = (
            "O sistema permite receber imagens enviadas pelo aparelho de ultrassom "
            "e vinculá-las ao exame do paciente."
        )
        template = "Prazo de liberação: acesso em até 24 horas.\n\n" + descricao
        paragrafos = paragrafos_condicoes(template, _Oportunidade([descricao]))
        self.assertEqual(paragrafos, ["Prazo de liberação: acesso em até 24 horas."])

    def test_subtitulo_acompanha_a_versao_contratada(self):
        from types import SimpleNamespace

        from crm_vendas.pdf_proposta_contrato.formatters import subtitulo_da_versao

        def item(nome, recorrencia="mensal"):
            return SimpleNamespace(produto_servico=SimpleNamespace(nome=nome, recorrencia=recorrencia))

        self.assertEqual(
            subtitulo_da_versao([
                item("ULTRASIS LAUDOS BÁSICO"),
                item("Captura de imagens DICOM"),
                item("DICOM Worklist • 1 aparelho"),
                item("Implantação DICOM e Worklist", "unico"),
            ]),
            "Sistema de Laudos • Captura DICOM • Worklist",
        )
        self.assertEqual(
            subtitulo_da_versao([item("Sistema de laudos avançado")]),
            "Sistema de Laudos",
        )
        self.assertEqual(
            subtitulo_da_versao([item("ULTRASIS CLÍNICA 1 A 4 PROFISSIONAIS - POR PROFISSIONAL")]),
            "Sistema de Clínica",
        )

    def test_coluna_de_valor_unitario_so_quando_a_quantidade_passa_de_um(self):
        from types import SimpleNamespace

        from crm_vendas.pdf_proposta_contrato.sections import _mostra_valor_unitario

        um = SimpleNamespace(quantidade=1)
        tres = SimpleNamespace(quantidade=3)
        self.assertFalse(_mostra_valor_unitario([um, um]))
        self.assertTrue(_mostra_valor_unitario([um, tres]))
