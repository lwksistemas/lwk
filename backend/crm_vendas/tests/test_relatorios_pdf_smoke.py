"""Smoke tests: geração de PDF de relatórios de vendas."""
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

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
