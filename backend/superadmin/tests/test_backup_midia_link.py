from django.test import SimpleTestCase, override_settings

from superadmin.backup_midia_link import (
    decodificar_token_backup_midia,
    gerar_token_backup_midia,
    url_pagina_backup_midia,
)


class BackupMidiaLinkTest(SimpleTestCase):
    def test_token_ida_e_volta(self):
        token = gerar_token_backup_midia(loja_id=6, slug="clinicaharmonis")
        payload = decodificar_token_backup_midia(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["loja_id"], 6)
        self.assertEqual(payload["slug"], "clinicaharmonis")

    def test_token_invalido(self):
        self.assertIsNone(decodificar_token_backup_midia("nao-e-token"))
        self.assertIsNone(decodificar_token_backup_midia(""))

    def test_url_usa_frontend(self):
        loja = type("Loja", (), {"id": 6, "slug": "clinicaharmonis"})()
        with override_settings(FRONTEND_URL="https://lwksistemas.com.br"):
            url = url_pagina_backup_midia(loja)
        self.assertTrue(url.startswith("https://lwksistemas.com.br/backup-midia/"))
