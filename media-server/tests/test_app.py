"""Testes do media-server (token por loja, pasta e URL assinada)."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as media_app  # noqa: E402


class MediaServerAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        media_app.STORAGE_ROOT = Path(self.tmp.name)
        media_app.API_TOKEN = "master-test"
        media_app.REQUIRE_SIGNED = False
        self.client = media_app.app.test_client()
        self.felix = "41449198000172"
        self.harmonis = "37302743000126"

    def tearDown(self):
        self.tmp.cleanup()

    def _upload(self, tenant: str, token: str, folder="admin/fotos", filename="a.jpg", body=b"xx"):
        return self.client.post(
            f"/upload/{tenant}/",
            headers={"Authorization": f"Bearer {token}"},
            data={"folder": folder, "file": (io.BytesIO(body), filename)},
            content_type="multipart/form-data",
        )

    def test_token_da_loja_nao_escreve_na_outra(self):
        token_felix = media_app.token_for_tenant(self.felix)
        resp = self._upload(self.harmonis, token_felix)
        self.assertEqual(resp.status_code, 401)

    def test_token_da_loja_escreve_na_propria(self):
        token = media_app.token_for_tenant(self.harmonis)
        resp = self._upload(self.harmonis, token)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("/files/37302743000126/admin/fotos/", resp.get_json()["url"])

    def test_master_lista_tenants_token_loja_nao(self):
        token = media_app.token_for_tenant(self.harmonis)
        recusado = self.client.get("/list/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(recusado.status_code, 401)
        ok = self.client.get("/list/", headers={"Authorization": "Bearer master-test"})
        self.assertEqual(ok.status_code, 200)

    def test_recusa_pdf_em_pasta_de_fotos(self):
        resp = self._upload(
            self.harmonis, "master-test", folder="admin/fotos", filename="x.pdf", body=b"%PDF"
        )
        self.assertEqual(resp.status_code, 400)

    def test_auth_file_sem_assinatura_libera_quando_nao_exige(self):
        resp = self.client.get(
            "/auth-file",
            headers={"X-Original-URI": "/files/37302743000126/admin/fotos/a.jpg"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_auth_file_exige_assinatura_quando_ligado(self):
        media_app.REQUIRE_SIGNED = True
        resp = self.client.get(
            "/auth-file",
            headers={"X-Original-URI": "/files/37302743000126/admin/fotos/a.jpg"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_auth_file_aceita_hmac_valido(self):
        media_app.REQUIRE_SIGNED = True
        path = "/files/37302743000126/admin/fotos/a.jpg"
        exp = 2_000_000_000
        sig = media_app._assinatura_path(path, exp)
        resp = self.client.get(
            "/auth-file",
            headers={"X-Original-URI": f"{path}?e={exp}&s={sig}"},
        )
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
