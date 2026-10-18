"""Smoke tests: geração de PDF de relatórios de vendas."""
from datetime import date, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from crm_vendas.relatorios_negociacao_pdf import (
    gerar_relatorio_negociacao_ganhos,
    nome_do_cliente,
    telefone_do_cliente,
    telefone_para_exibicao,
)
from crm_vendas.relatorios_vendas_pdf import gerar_relatorio_vendas_total
from crm_vendas.relatorios_vendas_pdf_helpers import merge_detalhamento_vendedores_pdf


class RelatoriosPdfSmokeTest(SimpleTestCase):
    def _mock_oportunidades_chain(self):
        chain = MagicMock()
        chain.filter.return_value = chain
        chain.select_related.return_value = chain
        chain.aggregate.return_value = {
            "total_vendas": 0,
            "total_comissoes": 0,
            "quantidade": 0,
        }
        values_chain = MagicMock()
        values_chain.annotate.return_value = []
        chain.values.return_value = values_chain
        return chain

    @patch("crm_vendas.relatorios_vendas_pdf.get_vendedor_destino_merge_loja", return_value=None)
    @patch("crm_vendas.relatorios_vendas_pdf._obter_logo_loja", return_value=None)
    @patch("crm_vendas.relatorios_vendas_pdf.calcular_periodo", return_value=(date(2026, 6, 1), date(2026, 6, 30)))
    @patch("crm_vendas.relatorios_vendas_pdf.Oportunidade")
    def test_gerar_relatorio_vendas_total_retorna_pdf(
        self,
        mock_opp,
        _periodo,
        _logo,
        _merge,
    ):
        mock_opp.objects.filter.return_value = self._mock_oportunidades_chain()

        buffer = gerar_relatorio_vendas_total(loja_id=1, periodo="mes_atual")

        self.assertIsInstance(buffer, BytesIO)
        data = buffer.getvalue()
        self.assertGreater(len(data), 100)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_merge_detalhamento_soma_sem_vendedor_no_destino(self):
        destino = MagicMock()
        destino.id = 5
        destino.nome = "ADMIN"

        raw = [
            {"vendedor_id": 5, "vendedor__nome": "ADMIN", "vendedor__is_active": True, "total": 100, "comissao": 10, "qtd": 1},
            {"vendedor_id": None, "vendedor__nome": None, "vendedor__is_active": None, "total": 50, "comissao": 5, "qtd": 1},
        ]
        with patch("crm_vendas.relatorios_vendas_pdf_helpers.get_vendedor_destino_merge_loja", return_value=destino):
            merged = merge_detalhamento_vendedores_pdf(1, raw)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["vendedor_id"], 5)
        self.assertEqual(merged[0]["total"], 150.0)
        self.assertEqual(merged[0]["qtd"], 2)


class RelatorioNegociacaoGanhosTest(SimpleTestCase):
    def test_telefone_prefere_o_do_lead(self):
        opp = SimpleNamespace(
            titulo="Venda",
            lead=SimpleNamespace(
                nome="Ana",
                telefone="11911112222",
                contato=SimpleNamespace(telefone="11000000000"),
                conta=SimpleNamespace(telefone="1133334444"),
            ),
        )
        self.assertEqual(nome_do_cliente(opp), "Ana")
        self.assertEqual(telefone_do_cliente(opp), "11911112222")
        self.assertEqual(telefone_para_exibicao(opp), "(11) 91111-2222")

    def test_telefone_com_codigo_55_sai_com_ddd(self):
        opp = SimpleNamespace(
            lead=SimpleNamespace(nome="Ana", telefone="5568984093985", contato=None, conta=None),
        )
        self.assertEqual(telefone_para_exibicao(opp), "(68) 98409-3985")

    @patch("crm_vendas.relatorios_negociacao_pdf._obter_logo_loja", return_value=None)
    @patch("crm_vendas.relatorios_negociacao_pdf.calcular_periodo", return_value=(date(2026, 10, 1), date(2026, 10, 31)))
    @patch("crm_vendas.relatorios_negociacao_pdf.Oportunidade")
    def test_pdf_traz_cliente_telefone_e_historico(self, mock_opp, _periodo, _logo):
        quando = timezone.make_aware(datetime(2026, 10, 2, 9, 0))
        nota = SimpleNamespace(
            created_at=quando,
            tipo="resposta_cliente",
            autor_nome="Ana",
            texto="Pode fechar.",
        )
        opp = SimpleNamespace(
            titulo="Implantação",
            valor=500,
            data_fechamento_ganho=date(2026, 10, 3),
            data_fechamento=None,
            feedback_pos_venda="",
            vendedor=SimpleNamespace(nome="Carlos"),
            lead=SimpleNamespace(nome="Ana Lima", telefone="16999990000", contato=None, conta=None),
            notas_negociacao=SimpleNamespace(all=lambda: [nota]),
        )
        chain = MagicMock()
        chain.filter.return_value = chain
        chain.select_related.return_value = chain
        chain.prefetch_related.return_value = chain
        chain.order_by.return_value = [opp]
        mock_opp.objects.filter.return_value = chain

        buffer = gerar_relatorio_negociacao_ganhos(loja_id=4, periodo="mes_atual")
        data = buffer.getvalue()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 100)
