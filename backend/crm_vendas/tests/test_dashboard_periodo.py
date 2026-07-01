"""Testes do filtro de período no dashboard CRM."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.test import TestCase


class TestDashboardPipelinePeriodo(TestCase):
    def test_pipeline_aberto_respeita_mes_atual(self):
        from crm_vendas.services_dashboard import build_dashboard_payload

        mock_opp = MagicMock()
        mock_opp.objects.all.return_value = mock_opp
        mock_opp.objects.filter.return_value = mock_opp
        mock_opp.filter.return_value = mock_opp
        mock_opp.distinct.return_value = mock_opp
        mock_opp.aggregate.side_effect = [
            {
                'total_oportunidades': 32,
                'receita': 0,
                'pipeline_aberto': 0,
                'oportunidades_em_andamento': 0,
                'total_fechados': 0,
                'total_ganhos': 0,
                'valor_perdido': 0,
            },
            {'total': 0},
            {'receita': 0, 'comissao': 0},
        ]
        mock_opp.values.return_value.annotate.return_value = []

        mock_lead = MagicMock()
        mock_lead.objects.all.return_value = mock_lead
        mock_lead.filter.return_value = mock_lead
        mock_lead.distinct.return_value = mock_lead
        mock_lead.count.return_value = 0

        mock_ativ = MagicMock()
        mock_ativ.objects.all.return_value = mock_ativ
        mock_ativ.filter.return_value = mock_ativ
        mock_ativ.distinct.return_value = mock_ativ

        mock_vend = MagicMock()
        mock_vend.objects.filter.return_value = mock_vend
        mock_vend.annotate.return_value = []

        with patch('crm_vendas.services_dashboard.timezone') as mock_tz, patch(
            'crm_vendas.models.Lead', mock_lead
        ), patch('crm_vendas.models.Oportunidade', mock_opp), patch(
            'crm_vendas.models.Atividade', mock_ativ
        ), patch(
            'crm_vendas.models.Vendedor', mock_vend
        ), patch(
            'crm_vendas.services_dashboard._fetch_proximas_atividades', return_value=[]
        ), patch(
            'crm_vendas.services_dashboard.get_vendedor_destino_merge_loja', return_value=None
        ):
            mock_tz.now.return_value.date.return_value = date(2026, 7, 1)
            out = build_dashboard_payload(
                1,
                None,
                'mes_atual',
                None,
                None,
                None,
                'todas',
                True,
            )

        self.assertEqual(out['pipeline_aberto'], 0)
        self.assertEqual(out['oportunidades_em_andamento'], 0)
        self.assertTrue(all(p['valor'] == 0 and p['quantidade'] == 0 for p in out['pipeline_por_etapa']))
        mock_opp.filter.assert_called()
