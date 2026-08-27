"""Cache de sessão única não pode expulsar o aparelho que acabou de logar."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from superadmin import authentication as auth
from superadmin.authentication import SessionAwareJWTAuthentication, invalidate_session_cache


class SessionAuthCacheTests(SimpleTestCase):
    def setUp(self):
        invalidate_session_cache()

    def tearDown(self):
        invalidate_session_cache()

    def test_sid_mismatch_consulta_db_em_vez_de_rejeitar_pelo_cache(self):
        """Worker A ainda tem o sid do desktop; o celular já gravou sid novo no DB."""
        user_id = 9
        sid_desktop = "sid-desktop-antigo"
        sid_celular = "sid-celular-novo"
        auth._session_cache[user_id] = (sid_desktop, 1_000_000.0)

        session = MagicMock()
        session.session_id = sid_celular
        session.is_expired.return_value = False

        authenticator = SessionAwareJWTAuthentication()
        with (
            patch("superadmin.models.UserSession.objects.filter") as mock_filter,
            patch("time.time", return_value=1_000_000.5),
        ):
            mock_filter.return_value.first.return_value = session
            result = authenticator._validate_with_cache(user_id, sid_celular)

        self.assertEqual(result, {"valid": True})
        self.assertEqual(auth._session_cache[user_id][0], sid_celular)

    def test_sid_igual_aceita_sem_consultar_db(self):
        user_id = 9
        sid = "sid-atual"
        auth._session_cache[user_id] = (sid, 1_000_000.0)

        authenticator = SessionAwareJWTAuthentication()
        with patch("superadmin.models.UserSession.objects.filter") as mock_filter:
            with patch("time.time", return_value=1_000_000.5):
                result = authenticator._validate_with_cache(user_id, sid)

        self.assertEqual(result, {"valid": True})
        mock_filter.assert_not_called()

    def test_sid_divergente_no_db_ainda_rejeita(self):
        user_id = 9
        auth._session_cache[user_id] = ("sid-antigo", 1_000_000.0)

        session = MagicMock()
        session.session_id = "sid-do-outro-dispositivo"
        session.is_expired.return_value = False

        authenticator = SessionAwareJWTAuthentication()
        with (
            patch("superadmin.models.UserSession.objects.filter") as mock_filter,
            patch("time.time", return_value=1_000_000.5),
        ):
            mock_filter.return_value.first.return_value = session
            result = authenticator._validate_with_cache(user_id, "sid-deste-dispositivo")

        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "DIFFERENT_SESSION")
