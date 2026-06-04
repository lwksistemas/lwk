from django.test import SimpleTestCase

from core.mfa_backup import (
    backup_codes_remaining,
    generate_backup_codes,
    issue_backup_codes,
    verify_and_consume_backup_code,
)


class MfaBackupTests(SimpleTestCase):
    def test_generate_format(self):
        codes = generate_backup_codes(3)
        self.assertEqual(len(codes), 3)
        for code in codes:
            self.assertRegex(code, r'^[A-Z2-9]{4}-[A-Z2-9]{4}$')

    def test_issue_and_consume_single_use(self):
        plain, encrypted = issue_backup_codes(2)
        self.assertEqual(len(plain), 2)
        self.assertEqual(backup_codes_remaining(encrypted), 2)

        ok, new_blob = verify_and_consume_backup_code(encrypted, plain[0])
        self.assertTrue(ok)
        self.assertEqual(backup_codes_remaining(new_blob), 1)

        ok2, _ = verify_and_consume_backup_code(new_blob, plain[0])
        self.assertFalse(ok2)

        ok3, final = verify_and_consume_backup_code(new_blob, plain[1])
        self.assertTrue(ok3)
        self.assertEqual(backup_codes_remaining(final), 0)

    def test_rejects_short_or_wrong_code(self):
        _, encrypted = issue_backup_codes(1)
        self.assertFalse(verify_and_consume_backup_code(encrypted, 'AB')[0])
        self.assertFalse(verify_and_consume_backup_code(encrypted, 'ZZZZ-ZZZZ')[0])
