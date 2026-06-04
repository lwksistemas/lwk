from django.test import SimpleTestCase

from core.mfa_service import generate_totp_secret, verify_totp_code

try:
    import pyotp
except ImportError:
    pyotp = None


class MfaServiceTests(SimpleTestCase):
    def test_totp_roundtrip(self):
        if pyotp is None:
            self.skipTest('pyotp não instalado')
        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        self.assertTrue(verify_totp_code(secret, code))

    def test_rejects_wrong_code(self):
        if pyotp is None:
            self.skipTest('pyotp não instalado')
        secret = generate_totp_secret()
        self.assertFalse(verify_totp_code(secret, '000000'))
