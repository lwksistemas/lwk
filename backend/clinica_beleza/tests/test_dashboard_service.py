"""Testes unitários do service de dashboard."""
from datetime import date

from django.test import SimpleTestCase

from clinica_beleza.dashboard_service import (
    dashboard_filter_meta,
    next_appointments_limit,
    parse_dashboard_period,
    parse_next_appointments_period,
    parse_professional_id,
)


class ParseDashboardPeriodTests(SimpleTestCase):
    def test_mes_atual_termina_em_hoje(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=6, ano=2026, today=today)
        self.assertEqual(start, date(2026, 6, 1))
        self.assertEqual(end, today)
        self.assertEqual(mes, 6)
        self.assertEqual(ano, 2026)

    def test_mes_passado_usa_ultimo_dia(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=3, ano=2026, today=today)
        self.assertEqual(start, date(2026, 3, 1))
        self.assertEqual(end, date(2026, 3, 31))
        self.assertEqual(mes, 3)

    def test_mes_invalido_cai_no_mes_atual(self):
        today = date(2026, 6, 20)
        start, end, mes, ano = parse_dashboard_period(mes=99, ano=2026, today=today)
        self.assertEqual(mes, today.month)
        self.assertEqual(ano, today.year)
        self.assertEqual(start, date(2026, 6, 1))
        self.assertEqual(end, today)


class DashboardFilterMetaTests(SimpleTestCase):
    def test_label_mes_ano(self):
        meta = dashboard_filter_meta(
            filter_mes=6,
            filter_ano=2026,
            today=date(2026, 6, 15),
            period_start=date(2026, 6, 1),
            period_end=date(2026, 6, 15),
        )
        self.assertEqual(meta['label'], 'Junho/2026')
        self.assertTrue(meta['is_current_month'])
        self.assertEqual(meta['period_start'], '2026-06-01')


class DashboardQueryParamParsingTests(SimpleTestCase):
    def test_period_default(self):
        self.assertEqual(parse_next_appointments_period(None), 'proximos')

    def test_professional_id_invalido(self):
        self.assertIsNone(parse_professional_id('abc'))

    def test_next_appointments_limit(self):
        self.assertEqual(next_appointments_limit('hoje'), 10)
        self.assertEqual(next_appointments_limit('semana'), 15)
