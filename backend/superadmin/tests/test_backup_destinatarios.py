from django.test import SimpleTestCase

from superadmin.backup_destinatarios import filtrar_emails_backup


class FiltrarEmailsBackupTest(SimpleTestCase):
    def test_vendedor_comum_nao_recebe(self):
        emails = filtrar_emails_backup(
            "admin@loja.com",
            [
                {"email": "vendedor@loja.com", "recebe_backup": False},
                {"email": "admin@loja.com", "recebe_backup": False},
            ],
        )
        self.assertEqual(emails, ["admin@loja.com"])

    def test_perfil_administrador_recebe_junto_com_o_sistema(self):
        emails = filtrar_emails_backup(
            "admin@loja.com",
            [
                {"email": "ana@loja.com", "recebe_backup": True},
                {"email": "vendedor@loja.com", "recebe_backup": False},
            ],
        )
        self.assertEqual(emails, ["admin@loja.com", "ana@loja.com"])

    def test_nao_repete_o_mesmo_e_mail(self):
        emails = filtrar_emails_backup(
            "admin@loja.com",
            [{"email": "Admin@loja.com", "recebe_backup": True}],
        )
        self.assertEqual(emails, ["admin@loja.com"])
