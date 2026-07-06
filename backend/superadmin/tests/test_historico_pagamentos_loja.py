from django.test import SimpleTestCase

from superadmin.financeiro_views.helpers import (
    _deduplicar_historico_pagamentos,
    _suprimir_pendentes_obsoletos_historico,
)


class DeduplicarHistoricoPagamentosTest(SimpleTestCase):
    def test_remove_cobranca_aberta_duplicada_mesmo_asaas_id(self):
        historico = [
            {
                'pagamento_loja_id': 10,
                'id': 10,
                'asaas_id': 'pay_abc',
                'valor': 7.0,
                'data_vencimento': '2026-07-06',
                'is_pending': True,
                'is_overdue': False,
                'boleto_url': '',
            },
            {
                'pagamento_loja_id': 11,
                'id': 11,
                'asaas_id': 'pay_abc',
                'valor': 7.0,
                'data_vencimento': '2026-07-06',
                'is_pending': True,
                'is_overdue': False,
                'boleto_url': 'https://boleto.example',
            },
        ]
        out = _deduplicar_historico_pagamentos(historico)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['pagamento_loja_id'], 11)
        self.assertEqual(out[0]['boleto_url'], 'https://boleto.example')

    def test_remove_duplicata_mesma_data_e_valor_em_aberto(self):
        historico = [
            {
                'pagamento_loja_id': 20,
                'id': 20,
                'asaas_id': '',
                'valor': 7.0,
                'data_vencimento': '2026-07-06',
                'is_pending': True,
                'is_overdue': False,
                'boleto_url': 'https://boleto.example',
            },
            {
                'pagamento_loja_id': 21,
                'id': 21,
                'asaas_id': '',
                'valor': 7.0,
                'data_vencimento': '2026-07-06',
                'is_pending': True,
                'is_overdue': False,
                'boleto_url': '',
            },
        ]
        out = _deduplicar_historico_pagamentos(historico)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['pagamento_loja_id'], 20)

    def test_mantem_pagos_distintos(self):
        historico = [
            {
                'pagamento_loja_id': 1,
                'id': 1,
                'asaas_id': 'pay_1',
                'valor': 7.0,
                'data_vencimento': '2026-06-06',
                'is_pending': False,
                'is_overdue': False,
                'is_paid': True,
            },
            {
                'pagamento_loja_id': 2,
                'id': 2,
                'asaas_id': 'pay_2',
                'valor': 7.0,
                'data_vencimento': '2026-07-06',
                'is_pending': True,
                'is_overdue': False,
                'is_paid': False,
            },
        ]
        out = _deduplicar_historico_pagamentos(historico)
        self.assertEqual(len(out), 2)


class SuprimirPendentesObsoletosHistoricoTest(SimpleTestCase):
    def test_remove_pendente_quando_mesma_referencia_ja_paga(self):
        historico = [
            {
                'pagamento_loja_id': 1,
                'id': 1,
                'referencia_mes': '2026-06-01',
                'data_vencimento': '2026-07-03',
                'valor': 7.0,
                'is_paid': True,
                'is_pending': False,
                'is_overdue': False,
            },
            {
                'pagamento_loja_id': 2,
                'id': 2,
                'referencia_mes': '2026-06-01',
                'data_vencimento': '2026-07-03',
                'valor': 7.0,
                'is_paid': False,
                'is_pending': True,
                'is_overdue': False,
            },
        ]
        out = _suprimir_pendentes_obsoletos_historico(historico)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]['is_paid'])

    def test_mantem_pendente_de_outro_mes(self):
        historico = [
            {
                'pagamento_loja_id': 1,
                'id': 1,
                'referencia_mes': '2026-06-01',
                'data_vencimento': '2026-07-03',
                'valor': 7.0,
                'is_paid': True,
                'is_pending': False,
                'is_overdue': False,
            },
            {
                'pagamento_loja_id': 2,
                'id': 2,
                'referencia_mes': '2026-07-01',
                'data_vencimento': '2026-08-03',
                'valor': 7.0,
                'is_paid': False,
                'is_pending': True,
                'is_overdue': False,
            },
        ]
        out = _suprimir_pendentes_obsoletos_historico(historico)
        self.assertEqual(len(out), 2)
