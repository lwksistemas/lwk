"""Testes do módulo unificado de períodos do CRM."""
from datetime import date
from unittest.mock import patch

from django.test import TestCase


class TestPeriodoUnificado(TestCase):
    def test_trimestre_rolante_tres_meses(self):
        from crm_vendas.periodo import calcular_intervalo_datas

        with patch('crm_vendas.periodo.timezone') as mock_tz:
            mock_tz.now.return_value.date.return_value = date(2026, 7, 15)
            inicio, fim = calcular_intervalo_datas('trimestre_atual')
        self.assertEqual(inicio, date(2026, 5, 1))
        self.assertEqual(fim, date(2026, 7, 15))

    def test_relatorios_usa_mesma_semantica_dashboard(self):
        from crm_vendas.periodo import calcular_intervalo_datas
        from crm_vendas.relatorios import calcular_periodo

        with patch('crm_vendas.periodo.timezone') as mock_tz:
            mock_tz.now.return_value.date.return_value = date(2026, 7, 15)
            dash = calcular_intervalo_datas('trimestre_atual')
            rel = calcular_periodo('trimestre_atual')
        self.assertEqual(dash, rel)

    def test_filtro_fechamento_com_prefixo(self):
        from django.db.models import Q

        from crm_vendas.periodo import filtro_fechamento_no_periodo
        from crm_vendas.relatorios import _filtro_datas_fechamento_ganho
        from crm_vendas.services_dashboard import _filtro_fechamento_no_periodo

        inicio, fim = date(2026, 1, 1), date(2026, 1, 31)
        self.assertEqual(
            _filtro_datas_fechamento_ganho(inicio, fim),
            filtro_fechamento_no_periodo(inicio, fim),
        )
        self.assertEqual(
            _filtro_fechamento_no_periodo(inicio, fim),
            filtro_fechamento_no_periodo(inicio, fim),
        )
        prefixed = filtro_fechamento_no_periodo(inicio, fim, prefix='oportunidades')
        self.assertIsInstance(prefixed, Q)
