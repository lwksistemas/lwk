"""Testes — autenticação do webhook Evolution."""
import json
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from whatsapp.views_evolution_webhook import EvolutionWebhookView


class EvolutionWebhookAuthTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.body = json.dumps({'event': 'connection.update', 'instance': 'lwk_loja_1', 'data': {}})

    @override_settings(EVOLUTION_API_KEY='secret-key', DEBUG=False)
    def test_rejeita_sem_apikey(self):
        request = self.factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=self.body,
            content_type='application/json',
        )
        response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(EVOLUTION_API_KEY='secret-key', DEBUG=False)
    def test_aceita_com_apikey_correta(self):
        request = self.factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=self.body,
            content_type='application/json',
            HTTP_APIKEY='secret-key',
        )
        with patch('whatsapp.connection_service.update_evolution_connection_from_webhook'):
            response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(EVOLUTION_API_KEY='', DEBUG=False)
    def test_sem_key_em_producao_rejeita(self):
        request = self.factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=self.body,
            content_type='application/json',
        )
        response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(EVOLUTION_API_KEY='', DEBUG=True)
    def test_sem_key_em_debug_aceita(self):
        request = self.factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=self.body,
            content_type='application/json',
        )
        with patch('whatsapp.connection_service.update_evolution_connection_from_webhook'):
            response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(EVOLUTION_API_KEY='secret-key', DEBUG=False)
    def test_ip_railway_nao_bypassa_sem_apikey(self):
        """IP interno não substitui Apikey (allowlist removida)."""
        request = self.factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=self.body,
            content_type='application/json',
            REMOTE_ADDR='100.64.0.1',
        )
        response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 401)


class SetInstanceWebhookHeadersTest(SimpleTestCase):
    @override_settings(EVOLUTION_API_KEY='my-evolution-key')
    @patch('whatsapp.evolution_client._request', return_value={})
    @patch('whatsapp.evolution_client.evolution_webhook_url', return_value='https://api.example/webhook/')
    def test_registra_header_apikey_no_webhook(self, _url, mock_request):
        from whatsapp.evolution_client import set_instance_webhook

        set_instance_webhook('lwk_loja_6')

        body = mock_request.call_args[1]['json_body']
        self.assertEqual(body['webhook']['headers']['Apikey'], 'my-evolution-key')


class EvolutionWebhookBodyApikeyTest(SimpleTestCase):
    @override_settings(EVOLUTION_API_KEY='secret-key', DEBUG=False)
    def test_aceita_apikey_no_body_evolution(self):
        factory = RequestFactory()
        payload = {
            'event': 'connection.update',
            'instance': 'lwk_loja_1',
            'data': {},
            'apikey': 'secret-key',
        }
        request = factory.post(
            '/api/whatsapp/evolution/webhook/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        with patch('whatsapp.connection_service.update_evolution_connection_from_webhook'):
            response = EvolutionWebhookView.as_view()(request)
        self.assertEqual(response.status_code, 200)
