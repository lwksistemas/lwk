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

    def test_pdf_mantem_nome_enviado(self):
        dest = Path(self.tmp.name)
        nome = media_app.nome_arquivo_destino(
            "Pedido_01_PHD_DO_BRASIL.pdf", ".pdf", dest,
        )
        self.assertEqual(nome, "Pedido_01_PHD_DO_BRASIL.pdf")
        resp = self._upload(
            self.harmonis,
            "master-test",
            folder="admin/pdf",
            filename="Pedido_01_PHD_DO_BRASIL.pdf",
            body=b"%PDF-1.4 test",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["filename"], "Pedido_01_PHD_DO_BRASIL.pdf")
        self.assertIn("/admin/pdf/Pedido_01_PHD_DO_BRASIL.pdf", data["url"])

    def test_pdf_mesmo_nome_sobrescreve(self):
        dest = Path(self.tmp.name) / "dup"
        dest.mkdir()
        (dest / "termo.pdf").write_bytes(b"a")
        segundo = media_app.nome_arquivo_destino("termo.pdf", ".pdf", dest)
        self.assertEqual(segundo, "termo.pdf")

    def test_foto_continua_uuid(self):
        dest = Path(self.tmp.name)
        nome = media_app.nome_arquivo_destino("foto.jpg", ".jpg", dest)
        self.assertRegex(nome, r"^[a-f0-9]{32}\.jpg$")

    def test_pdf_ignora_path_no_nome(self):
        dest = Path(self.tmp.name)
        nome = media_app.nome_arquivo_destino("../../etc/passwd.pdf", ".pdf", dest)
        self.assertEqual(nome, "passwd.pdf")


if __name__ == "__main__":
    unittest.main()
