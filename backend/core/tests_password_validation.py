from django.test import SimpleTestCase

from core.password_validation import validate_password_policy


class PasswordPolicyTests(SimpleTestCase):
    def test_accepts_strong_password(self):
        ok, msg = validate_password_policy('Senha123')
        self.assertTrue(ok)
        self.assertEqual(msg, '')

    def test_rejects_short(self):
        ok, msg = validate_password_policy('Ab1')
        self.assertFalse(ok)
        self.assertIn('mínimo', msg)

    def test_rejects_without_number(self):
        self.assertFalse(validate_password_policy('SomenteLetras')[0])

    def test_rejects_without_letter(self):
        self.assertFalse(validate_password_policy('12345678')[0])
