"""get_credentials: só apaga a conexão em erro DEFINITIVO (invalid_grant).
Erro transitório (rede/5xx) mantém a conexão e pede para tentar de novo.
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from google.auth.exceptions import RefreshError

from crm_vendas.google_calendar_service import get_credentials


def _conn():
    c = MagicMock()
    c.access_token = "velho"
    c.refresh_token = "refresh-abc"
    # expirado (ontem)
    c.token_expiry = datetime.now(dt_timezone.utc) - timedelta(days=1)
    return c


@override_settings(GOOGLE_CLIENT_ID="cid", GOOGLE_CLIENT_SECRET="sec")
class GetCredentialsRefreshTest(SimpleTestCase):
    @patch("google.oauth2.credentials.Credentials.refresh")
    def test_erro_definitivo_apaga_conexao(self, mock_refresh):
        mock_refresh.side_effect = RefreshError("invalid_grant: Token has been expired or revoked.")
        conn = _conn()
        with self.assertRaises(ValueError) as ctx:
            get_credentials(conn)
        conn.delete.assert_called_once()
        self.assertIn("Desconecte e conecte", str(ctx.exception))

    @patch("google.oauth2.credentials.Credentials.refresh")
    def test_erro_transitorio_mantem_conexao(self, mock_refresh):
        mock_refresh.side_effect = RefreshError("Service unavailable (503)")
        conn = _conn()
        with self.assertRaises(ValueError) as ctx:
            get_credentials(conn)
        conn.delete.assert_not_called()
        self.assertIn("Tente sincronizar novamente", str(ctx.exception))
