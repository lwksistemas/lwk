"""Testes do webhook Asaas por loja (CRM)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from crm_vendas.asaas_loja_webhook_process import (
    invoice_payload_para_sync,
    process_asaas_loja_webhook_sync,
)


class InvoicePayloadParaSyncTest(SimpleTestCase):
    def test_invoice_direto_no_payload(self):
        payload = {
            'event': 'INVOICE_AUTHORIZED',
            'invoice': {'id': 'inv_1', 'status': 'AUTHORIZED'},
        }
        event, invoice = invoice_payload_para_sync(payload)
        self.assertEqual(event, 'INVOICE_AUTHORIZED')
        self.assertEqual(invoice['id'], 'inv_1')

    def test_invoice_aninhado_em_payment(self):
        payload = {
            'type': 'PAYMENT_RECEIVED',
            'payment': {
                'id': 'pay_1',
                'invoice': {'id': 'inv_2', 'status': 'SCHEDULED'},
            },
        }
        event, invoice = invoice_payload_para_sync(payload)
        self.assertEqual(event, 'PAYMENT_RECEIVED')
        self.assertEqual(invoice['id'], 'inv_2')

    def test_invoice_id_em_payment_sem_objeto_invoice(self):
        payload = {
            'event': 'PAYMENT_CONFIRMED',
            'payment': {'id': 'pay_2', 'invoiceId': 'inv_3', 'invoiceStatus': 'AUTHORIZED'},
        }
        event, invoice = invoice_payload_para_sync(payload)
        self.assertEqual(invoice['id'], 'inv_3')
        self.assertEqual(invoice['status'], 'AUTHORIZED')

    def test_sem_invoice_retorna_vazio(self):
        event, invoice = invoice_payload_para_sync({'event': 'PAYMENT_CREATED'})
        self.assertEqual(event, 'PAYMENT_CREATED')
        self.assertEqual(invoice, {})


@override_settings(DATABASES={'default': {}, 'loja_test': {}})
class ProcessAsaasLojaWebhookSyncTest(SimpleTestCase):
    def _loja(self, loja_id=4):
        loja = MagicMock()
        loja.id = loja_id
        loja.slug = 'felix'
        loja.database_name = 'loja_test'
        return loja

    @patch('core.db_config.ensure_loja_database_config', return_value=False)
    @patch('superadmin.models.Loja')
    def test_loja_inexistente_nao_quebra(self, mock_loja_cls, _ensure):
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = None
        process_asaas_loja_webhook_sync(99, {'event': 'PAYMENT_RECEIVED'})
        _ensure.assert_not_called()

    @patch('tenants.middleware.set_current_tenant_db')
    @patch('tenants.middleware.set_current_loja_id')
    @patch('core.db_config.ensure_loja_database_config', return_value=False)
    @patch('superadmin.models.Loja')
    def test_schema_indisponivel_para_cedo(self, mock_loja_cls, _ensure, mock_set_loja, mock_set_db):
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = self._loja()
        process_asaas_loja_webhook_sync(4, {'event': 'PAYMENT_RECEIVED'})
        mock_set_loja.assert_not_called()
        mock_set_db.assert_not_called()

    @patch('crm_vendas.services_relatorio_comissao.processar_pagamento_comissao')
    @patch('crm_vendas.models_relatorio_comissao.RelatorioComissao')
    @patch('nfse_integration.asaas_webhook_sync.sincronizar_nfse_com_webhook_invoice')
    @patch('tenants.middleware.set_current_tenant_db')
    @patch('tenants.middleware.set_current_loja_id')
    @patch('core.db_config.ensure_loja_database_config', return_value=True)
    @patch('superadmin.models.Loja')
    def test_pagamento_confirmado_processa_comissao(
        self,
        mock_loja_cls,
        _ensure,
        _set_loja,
        _set_db,
        mock_nfse,
        mock_rc_cls,
        mock_processar,
    ):
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = self._loja()
        relatorio = MagicMock()
        mock_rc_cls.objects.filter.return_value.first.return_value = relatorio

        process_asaas_loja_webhook_sync(
            4,
            {
                'event': 'PAYMENT_CONFIRMED',
                'payment': {'id': 'pay_rc_1'},
                'invoice': {'id': 'inv_1'},
            },
        )

        mock_nfse.assert_called_once()
        mock_processar.assert_called_once_with(relatorio)

    @patch('crm_vendas.services_relatorio_comissao.processar_pagamento_comissao')
    @patch('crm_vendas.models_relatorio_comissao.RelatorioComissao')
    @patch('nfse_integration.asaas_webhook_sync.sincronizar_nfse_com_webhook_invoice')
    @patch('tenants.middleware.set_current_tenant_db')
    @patch('tenants.middleware.set_current_loja_id')
    @patch('core.db_config.ensure_loja_database_config', return_value=True)
    @patch('superadmin.models.Loja')
    def test_pagamento_sem_relatorio_nao_chama_processar(
        self,
        mock_loja_cls,
        _ensure,
        _set_loja,
        _set_db,
        mock_nfse,
        mock_rc_cls,
        mock_processar,
    ):
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = self._loja()
        mock_rc_cls.objects.filter.return_value.first.return_value = None

        process_asaas_loja_webhook_sync(
            4,
            {'event': 'PAYMENT_RECEIVED', 'payment': {'id': 'pay_sem_rc'}},
        )

        mock_nfse.assert_not_called()
        mock_processar.assert_not_called()
