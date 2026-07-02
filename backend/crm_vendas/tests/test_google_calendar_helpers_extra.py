"""Testes adicionais dos helpers Google Calendar."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from crm_vendas.google_calendar_helpers import (
    PULL_EVENTS_DAYS,
    get_redirect_uri,
    pull_events_time_range,
    redirect_calendario,
)


class GoogleCalendarHelpersExtraTest(SimpleTestCase):
    def test_pull_events_time_range(self):
        t_min, t_max = pull_events_time_range()
        self.assertLess(t_min, t_max)
        self.assertEqual((t_max - t_min).days, PULL_EVENTS_DAYS)

    @override_settings(DEBUG=True, FRONTEND_URL='https://app.test')
    def test_redirect_calendario_sucesso(self):
        response = redirect_calendario('felix', success=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('felix/crm-vendas/calendario', response.url)
        self.assertIn('google_connected=1', response.url)

    @override_settings(DEBUG=True, FRONTEND_URL='https://app.test')
    def test_redirect_calendario_erro(self):
        response = redirect_calendario('felix', success=False)
        self.assertIn('google_error=1', response.url)

    @override_settings(DEBUG=True)
    def test_get_redirect_uri_http_local(self):
        request = MagicMock()
        request.scheme = 'http'
        request.get_host.return_value = 'localhost:8000'
        request.META = {}
        uri = get_redirect_uri(request)
        self.assertIn('/api/crm-vendas/google-calendar/callback/', uri)
        self.assertTrue(uri.startswith('http://'))

    @override_settings(DEBUG=False)
    def test_get_redirect_uri_forca_https_producao(self):
        request = MagicMock()
        request.scheme = 'http'
        request.get_host.return_value = 'api.lwksistemas.com.br'
        request.META = {'HTTP_X_FORWARDED_PROTO': 'https'}
        uri = get_redirect_uri(request)
        self.assertTrue(uri.startswith('https://'))

    @patch('crm_vendas.google_calendar_helpers.GoogleCalendarConnection')
    def test_get_connection_filtra_vendedor(self, mock_conn):
        from crm_vendas.google_calendar_helpers import get_connection_for_loja_and_vendedor

        chain = mock_conn.objects.using.return_value.filter.return_value
        chain.filter.return_value.first.return_value = MagicMock()
        conn = get_connection_for_loja_and_vendedor(4, vendedor_id=7)
        self.assertIsNotNone(conn)
        mock_conn.objects.using.assert_called_with('default')
