"""PDF tabular de lançamentos, faturamento e comissões agrupadas."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.relatorio_tabela_pdf import (
    _fmt_iso_br,
    agrupar_comissoes_para_pdf,
    gerar_pdf_comissoes_agrupado,
    gerar_pdf_descontos,
    gerar_pdf_faturamento,
    gerar_pdf_lancamentos,
)


class FmtIsoBrTest(SimpleTestCase):
    def test_converte_iso(self):
        self.assertEqual(_fmt_iso_br("2026-09-18"), "18/09/2026")

    def test_vazio(self):
        self.assertEqual(_fmt_iso_br(None), "—")
        self.assertEqual(_fmt_iso_br(""), "—")


class AgruparComissoesPdfTest(SimpleTestCase):
    def setUp(self):
        self.resultado = {
            "profissionais": [{
                "nome": "Marina",
                "detalhes": [
                    {
                        "tipo_linha": "consulta",
                        "procedimento_nome": "Consulta",
                        "local_nome": "Sala 1",
                        "convenio_nome": "",
                        "qtd": 2,
                        "valor_consulta": 150,
                        "comissao_consulta": 30,
                        "valor_procedimento": 0,
                        "comissao_procedimento": 0,
                    },
                    {
                        "tipo_linha": "procedimento",
                        "procedimento_nome": "Botox",
                        "local_nome": "Sala 1",
                        "convenio_nome": "Particular",
                        "qtd": 1,
                        "valor_consulta": 0,
                        "comissao_consulta": 0,
                        "valor_procedimento": 990,
                        "comissao_procedimento": 99,
                    },
                ],
            }],
            "totais": {"total_atendimentos": 2, "valor_total": 1140, "comissao_total": 129},
        }

    def test_agrupa_por_local(self):
        out = agrupar_comissoes_para_pdf(self.resultado, "local")
        self.assertEqual(len(out["linhas"]), 1)
        linha = out["linhas"][0]
        self.assertEqual(linha["nome"], "Sala 1")
        self.assertEqual(linha["total_atendimentos"], 2)
        self.assertEqual(linha["valor_consulta"], 150)
        self.assertEqual(linha["valor_procedimento"], 990)
        self.assertEqual(linha["comissao_total"], 129)

    def test_agrupa_por_convenio_consulta_sem_nome(self):
        out = agrupar_comissoes_para_pdf(self.resultado, "convenio")
        nomes = {ln["nome"] for ln in out["linhas"]}
        self.assertIn("Particular / sem convênio", nomes)
        self.assertIn("Particular", nomes)


class GerarPdfTabelaTest(SimpleTestCase):
    def setUp(self):
        self.loja = SimpleNamespace(id=1, nome="HARMONIS")
        self.patcher = patch(
            "clinica_beleza.relatorio_tabela_pdf._resolver_cabecalho_relatorio",
            return_value=("texto", self.loja),
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_lancamentos_gera_pdf(self):
        resultado = {
            "profissionais": [{
                "professional_id": 1,
                "nome": "Nayara",
                "total_atendimentos": 1,
                "valor_total": 150,
                "comissao_total": 0,
                "lancamentos": [{
                    "payment_id": 10,
                    "data": "2026-09-18",
                    "paciente": "LUIZ HENRIQUE FELIX",
                    "procedimentos": "Consulta",
                    "convenio": "Particular",
                    "forma_pagamento": "CASH",
                    "forma_pagamento_label": "Dinheiro",
                    "valor": 150,
                    "comissao": 0,
                }],
            }],
            "totais": {"total_atendimentos": 1, "valor_total": 150, "comissao_total": 0},
        }
        buf = gerar_pdf_lancamentos(
            resultado=resultado,
            loja=self.loja,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 18),
        )
        self.assertTrue(buf.getvalue().startswith(b"%PDF"))

    def test_lancamentos_vazio_gera_pdf(self):
        buf = gerar_pdf_lancamentos(
            resultado={"profissionais": [], "totais": {"total_atendimentos": 0, "valor_total": 0, "comissao_total": 0}},
            loja=self.loja,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 18),
        )
        self.assertTrue(buf.getvalue().startswith(b"%PDF"))

    def test_descontos_gera_pdf(self):
        resultado = {
            "profissionais": [{
                "professional_id": 1,
                "nome": "Marina",
                "total_atendimentos": 1,
                "desconto_total": 150,
                "valor_bruto": 450,
                "valor_liquido": 300,
                "lancamentos": [{
                    "payment_id": 22,
                    "data": "2026-09-18",
                    "paciente": "TAMIRES FURONI",
                    "procedimentos": "DEPILAÇÃO A LASER",
                    "convenio": "Particular",
                    "valor_bruto": 450,
                    "desconto": 150,
                    "valor_liquido": 300,
                }],
            }],
            "totais": {
                "total_atendimentos": 1,
                "desconto_total": 150,
                "valor_bruto": 450,
                "valor_liquido": 300,
            },
        }
        buf = gerar_pdf_descontos(
            resultado=resultado,
            loja=self.loja,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 18),
        )
        self.assertTrue(buf.getvalue().startswith(b"%PDF"))
        resultado = {
            "linhas": [{
                "nome": "Marina",
                "total_atendimentos": 3,
                "valor_consulta": 300,
                "valor_procedimento": 990,
                "valor_total": 1290,
            }],
            "totais": {
                "total_atendimentos": 3,
                "valor_consulta": 300,
                "valor_procedimento": 990,
                "valor_total": 1290,
            },
            "agrupamento": "profissional",
        }
        buf = gerar_pdf_faturamento(
            resultado=resultado,
            loja=self.loja,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 18),
            agrupar="profissional",
        )
        self.assertTrue(buf.getvalue().startswith(b"%PDF"))

    def test_comissoes_agrupado_gera_pdf(self):
        resultado = {
            "profissionais": [{
                "nome": "Marina",
                "detalhes": [{
                    "tipo_linha": "consulta",
                    "procedimento_nome": "Consulta",
                    "local_nome": "Sala 1",
                    "convenio_nome": "",
                    "qtd": 1,
                    "valor_consulta": 150,
                    "comissao_consulta": 0,
                    "valor_procedimento": 0,
                    "comissao_procedimento": 0,
                }],
            }],
            "totais": {
                "total_atendimentos": 1,
                "valor_consulta": 150,
                "comissao_consulta": 0,
                "valor_procedimento": 0,
                "comissao_procedimento": 0,
                "valor_total": 150,
                "comissao_total": 0,
            },
        }
        buf = gerar_pdf_comissoes_agrupado(
            resultado=resultado,
            loja=self.loja,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 18),
            agrupar="local",
        )
        self.assertTrue(buf.getvalue().startswith(b"%PDF"))
