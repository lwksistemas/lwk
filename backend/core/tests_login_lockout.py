from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from core.login_lockout import (
    check_account_locked,
    clear_login_failures,
    normalize_username,
    record_login_failure,
)


class LoginLockoutLogicTests(SimpleTestCase):
    def test_normalize_username(self):
        self.assertEqual(normalize_username("  Admin.User  "), "admin.user")
        self.assertEqual(normalize_username(""), "")

    @override_settings(LOGIN_MAX_FAILURES=3, LOGIN_LOCKOUT_MINUTES=15)
    @patch("superadmin.models.LoginLockout")
    def test_locks_after_max_failures(self, mock_model):
        row = MagicMock()
        row.failed_attempts = 0
        row.locked_until = None
        mock_model.objects.get_or_create.return_value = (row, True)
        mock_model.objects.filter.return_value.first.return_value = None

        user = "test.lockout@example"
        self.assertFalse(record_login_failure(user))
        self.assertFalse(record_login_failure(user))
        self.assertTrue(record_login_failure(user))
        self.assertIsNotNone(row.locked_until)

    @patch("superadmin.models.LoginLockout")
    def test_check_account_locked_active(self, mock_model):
        until = timezone.now() + timedelta(minutes=10)
        row = MagicMock(locked_until=until)
        mock_model.objects.filter.return_value.first.return_value = row

        locked = check_account_locked("user1")
        self.assertEqual(locked, until)

    @patch("superadmin.models.LoginLockout")
    def test_check_account_locked_expired_clears_row(self, mock_model):
        until = timezone.now() - timedelta(minutes=1)
        row = MagicMock(locked_until=until)
        mock_model.objects.filter.return_value.first.return_value = row

        self.assertIsNone(check_account_locked("user1"))
        row.delete.assert_called_once()

    @patch("superadmin.models.LoginLockout")
    def test_clear_login_failures(self, mock_model):
        clear_login_failures("User.X")
        mock_model.objects.filter.assert_called_with(username_key="user.x")
