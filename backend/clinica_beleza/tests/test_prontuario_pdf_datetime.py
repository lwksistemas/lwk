"""Testes — datas/horas nos PDFs do prontuário (fuso America/Sao_Paulo)."""
from datetime import UTC, datetime

from django.test import SimpleTestCase, override_settings

from clinica_beleza.prontuario_pdf.elements import _format_datetime_br


@override_settings(TIME_ZONE="America/Sao_Paulo", USE_TZ=True)
class FormatDatetimeBrTest(SimpleTestCase):
    def test_converte_utc_para_horario_brasil(self):
        utc = datetime(2026, 6, 27, 18, 30, tzinfo=UTC)
        self.assertEqual(_format_datetime_br(utc), "27/06/2026 15:30")

    def test_vazio_quando_none(self):
        self.assertEqual(_format_datetime_br(None), "")
