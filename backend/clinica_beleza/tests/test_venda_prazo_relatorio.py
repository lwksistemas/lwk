"""Relatório de venda a prazo por profissional."""
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.venda_prazo_relatorio_service import calcular_venda_prazo


def _pagamento(*, pid, nome, paciente, vencimento, total, pago, saldo, dia, patient_id=1, consulta_numero=None):
    professional = SimpleNamespace(nome=nome)
    patient = SimpleNamespace(nome=paciente, telefone="(16) 99999-0000")
    appt = SimpleNamespace(
        professional_id=pid,
        professional=professional,
        patient_id=patient_id,
        patient=patient,
        date=datetime(2026, 9, dia, 17, 0),
        consulta=SimpleNamespace(numero=consulta_numero) if consulta_numero else None,
    )
    return SimpleNamespace(
        id=pid * 10 + dia,
        appointment=appt,
        data_vencimento=vencimento,
        valor_total_efetivo=Decimal(total),
        amount=Decimal(total),
        valor_pago_parcelas=Decimal(pago),
        saldo_devedor=Decimal(saldo),
    )


class CalcularVendaPrazoTest(SimpleTestCase):
    @patch("clinica_beleza.venda_prazo_relatorio_service._procedimentos_nome_agendamento", return_value="Tirzepatida")
    @patch("clinica_beleza.venda_prazo_relatorio_service.payments_visiveis_financeiro")
    def test_agrupa_por_profissional_e_marca_vencido(self, mock_visiveis, _procs):
        vencida = _pagamento(
            pid=6, nome="Marina", paciente="FERNANDA",
            vencimento=date(2026, 9, 15), total="300", pago="0", saldo="300", dia=10,
        )
        em_dia = _pagamento(
            pid=1, nome="Nayara", paciente="ELZA",
            vencimento=date(2026, 10, 20), total="200", pago="50", saldo="150", dia=20,
        )
        quitada = _pagamento(
            pid=1, nome="Nayara", paciente="QUITADA",
            vencimento=date(2026, 10, 20), total="100", pago="100", saldo="0", dia=21,
        )
        filtrado = MagicMock()
        filtrado.filter.return_value = filtrado
        filtrado.__iter__ = MagicMock(return_value=iter([vencida, em_dia, quitada]))
        base = MagicMock()
        base.filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = filtrado
        mock_visiveis.return_value = base

        result = calcular_venda_prazo(
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 30),
            hoje=date(2026, 10, 1),
        )

        self.assertEqual(result["totais"]["total_vendas"], 2)
        self.assertEqual(result["totais"]["valor_aberto"], 450.0)
        self.assertEqual(result["totais"]["valor_pago"], 50.0)
        nomes = [p["nome"] for p in result["profissionais"]]
        self.assertEqual(nomes, ["Marina", "Nayara"])
        marina = result["profissionais"][0]["vendas"][0]
        self.assertEqual(marina["situacao"], "vencido")
        self.assertEqual(marina["dias_atraso"], 16)
        self.assertEqual(marina["paciente"], "FERNANDA")
        nayara = result["profissionais"][1]["vendas"][0]
        self.assertEqual(nayara["situacao"], "em_dia")
        self.assertEqual(nayara["valor_aberto"], 150.0)

    @patch("clinica_beleza.venda_prazo_relatorio_service._procedimentos_nome_agendamento", return_value="Drenagem")
    @patch("clinica_beleza.venda_prazo_relatorio_service.payments_visiveis_financeiro")
    def test_agrupa_consultas_do_mesmo_cliente(self, mock_visiveis, _procs):
        primeira = _pagamento(
            pid=2, nome="Bruna", paciente="RENATA COELHO",
            vencimento=date(2026, 11, 6), total="120", pago="0", saldo="120", dia=3,
            patient_id=318, consulta_numero=200,
        )
        segunda = _pagamento(
            pid=6, nome="Marina", paciente="RENATA COELHO",
            vencimento=date(2026, 11, 6), total="300", pago="0", saldo="300", dia=3,
            patient_id=318, consulta_numero=205,
        )
        filtrado = MagicMock()
        filtrado.filter.return_value = filtrado
        filtrado.__iter__ = MagicMock(return_value=iter([primeira, segunda]))
        base = MagicMock()
        base.filter.return_value.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = filtrado
        mock_visiveis.return_value = base

        result = calcular_venda_prazo(hoje=date(2026, 10, 8))

        self.assertEqual(len(result["clientes"]), 1)
        cliente = result["clientes"][0]
        self.assertEqual(cliente["nome"], "RENATA COELHO")
        self.assertEqual(cliente["total_consultas"], 2)
        self.assertEqual(cliente["valor_aberto"], 420.0)
        numeros = [c["consulta_numero"] for c in cliente["consultas"]]
        self.assertEqual(numeros, [200, 205])
        self.assertEqual(cliente["consultas"][0]["profissional"], "Bruna")
        self.assertEqual(cliente["consultas"][1]["profissional"], "Marina")
