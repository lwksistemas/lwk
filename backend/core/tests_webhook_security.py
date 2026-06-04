"""Testes de validação de webhooks."""
import hashlib
import hmac
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from core.webhook_security import (
    verify_asaas_access_token,
    verify_mercadopago_signature,
)


class AsaasWebhookSecurityTests(SimpleTestCase):
    @override_settings(ASAAS_WEBHOOK_TOKEN='secret-token', WEBHOOK_STRICT_VERIFY=True)
    def test_valid_token(self):
        request = MagicMock()
        request.headers = {'asaas-access-token': 'secret-token'}
        self.assertTrue(verify_asaas_access_token(request))

    @override_settings(ASAAS_WEBHOOK_TOKEN='secret-token', WEBHOOK_STRICT_VERIFY=True)
    def test_invalid_token(self):
        request = MagicMock()
        request.headers = {'asaas-access-token': 'wrong'}
        self.assertFalse(verify_asaas_access_token(request))


class MercadoPagoWebhookSecurityTests(SimpleTestCase):
    @override_settings(MERCADOPAGO_WEBHOOK_SECRET='mp-secret', WEBHOOK_STRICT_VERIFY=True)
    def test_valid_signature(self):
        data_id = '12345'
        ts = '1704908010'
        request_id = 'req-abc'
        manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
        v1 = hmac.new(b'mp-secret', manifest.encode(), hashlib.sha256).hexdigest()

        request = MagicMock()
        request.headers = {
            'x-signature': f'ts={ts},v1={v1}',
            'x-request-id': request_id,
        }
        request.GET = {'data.id': data_id}
        request.data = {}
        self.assertTrue(verify_mercadopago_signature(request))
