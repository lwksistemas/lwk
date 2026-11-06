"""A limpeza do log de WhatsApp cai no domingo às 3h."""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from whatsapp.tasks import proxima_limpeza_logs_whatsapp

SP = ZoneInfo("America/Sao_Paulo")


class ProximaLimpezaLogsWhatsappTest(SimpleTestCase):
    def test_quinta_aponta_o_domingo_seguinte_as_3h(self):
        agora = datetime(2026, 11, 5, 22, 56, tzinfo=SP)
        self.assertEqual(
            proxima_limpeza_logs_whatsapp(agora),
            datetime(2026, 11, 8, 3, 0, tzinfo=SP),
        )

    def test_domingo_antes_das_3h_e_o_mesmo_dia(self):
        agora = datetime(2026, 11, 8, 2, 0, tzinfo=SP)
        self.assertEqual(
            proxima_limpeza_logs_whatsapp(agora),
            datetime(2026, 11, 8, 3, 0, tzinfo=SP),
        )

    def test_domingo_depois_das_3h_vai_para_a_semana_seguinte(self):
        agora = datetime(2026, 11, 8, 3, 30, tzinfo=SP)
        self.assertEqual(
            proxima_limpeza_logs_whatsapp(agora),
            datetime(2026, 11, 15, 3, 0, tzinfo=SP),
        )
