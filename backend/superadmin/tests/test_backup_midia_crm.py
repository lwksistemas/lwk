from types import SimpleNamespace

from django.test import SimpleTestCase

from superadmin.backup_email_service import BackupEmailService
from superadmin.backup_helpers import backup_inclui_midia


class BackupMidiaCrmTests(SimpleTestCase):
    def test_crm_inclui_fotos_e_pdfs(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(codigo="CRMVND"))
        self.assertTrue(backup_inclui_midia(loja))

    def test_clinica_continua_sem_midia_no_anexo(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(codigo="CLIBEL"))
        self.assertFalse(backup_inclui_midia(loja))

    def test_email_do_crm_diz_que_o_zip_esta_completo(self):
        texto = BackupEmailService()._texto_conteudo(
            SimpleNamespace(nome="Felix"),
            "",
            True,
        )
        self.assertIn("backup completo", texto)
        self.assertIn("PDFs", texto)
        self.assertNotIn("não vão no anexo", texto)

    def test_email_da_clinica_mantem_o_link(self):
        texto = BackupEmailService()._texto_conteudo(
            SimpleNamespace(nome="Clinica"),
            "https://lwksistemas.com.br/backup-midia/abc",
            False,
        )
        self.assertIn("não vão no anexo", BackupEmailService()._paragrafo_conteudo(
            SimpleNamespace(nome="Clinica"),
            {"link_midia": "https://lwksistemas.com.br/backup-midia/abc"},
            False,
        ))
        self.assertIn("backup-midia/abc", texto)
        self.assertIn("único ZIP", texto)
