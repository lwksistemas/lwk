"""Telefone do relatório de inadimplentes sai no formato brasileiro."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.inadimplentes_relatorio_service import _serialize_linha, calcular_inadimplentes


class TelefoneInadimplentesTest(SimpleTestCase):
    def test_exibe_55_como_ddd_e_numero(self):
        patient = SimpleNamespace(id=1, nome="RENATA COELHO", telefone="5516997280874", email="")
        appointment = SimpleNamespace(patient=patient)
        payment = SimpleNamespace(
            id=10,
            appointment=appointment,
            data_vencimento=date(2026, 10, 24),
            saldo_devedor=120,
            amount=120,
            status="PENDING",
        )
        linha = _serialize_linha(payment, date(2026, 11, 22))
        self.assertEqual(linha["telefone"], "(16) 99728-0874")

    def test_mantem_telefone_ja_formatado(self):
        patient = SimpleNamespace(id=2, nome="PATRICIA", telefone="(16) 99789-9941", email="")
        appointment = SimpleNamespace(patient=patient)
        payment = SimpleNamespace(
            id=11,
            appointment=appointment,
            data_vencimento=date(2026, 10, 12),
            saldo_devedor=4950,
            amount=4950,
            status="PENDING",
        )
        linha = _serialize_linha(payment, date(2026, 11, 22))
        self.assertEqual(linha["telefone"], "(16) 99789-9941")

    @patch("clinica_beleza.inadimplentes_relatorio_service.queryset_inadimplentes")
    def test_lista_usa_telefone_formatado(self, mock_qs):
        patient = SimpleNamespace(id=3, nome="JOICE", telefone="5516997469453", email="")
        appointment = SimpleNamespace(patient=patient)
        payment = SimpleNamespace(
            id=12,
            appointment=appointment,
            data_vencimento=date(2026, 10, 30),
            saldo_devedor=1950,
            amount=1950,
            status="PENDING",
        )
        filtrado = mock_qs.return_value
        filtrado.select_related.return_value.order_by.return_value = [payment]
        resultado = calcular_inadimplentes(hoje=date(2026, 11, 22))
        self.assertEqual(resultado["linhas"][0]["telefone"], "(16) 99746-9453")
