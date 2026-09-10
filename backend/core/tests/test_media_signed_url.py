from unittest import TestCase
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from core.media_storage import (
    assinar_url_midia,
    media_token_for_tenant,
    verificar_assinatura_midia,
)


class AssinarUrlMidiaTest(TestCase):
    @patch("core.media_storage.MEDIA_API_TOKEN", "segredo-teste")
    def test_roundtrip_hmac(self):
        url = "https://media.lwksistemas.com.br/files/37302743000126/luiz_222/fotos/a.jpg"
        assinada = assinar_url_midia(url, ttl_seconds=600)
        self.assertTrue(assinada.startswith(url + "?"))
        self.assertTrue(verificar_assinatura_midia(assinada))
        qs = parse_qs(urlparse(assinada).query)
        self.assertEqual(len(qs["s"][0]), 32)

    @patch("core.media_storage.MEDIA_API_TOKEN", "segredo-teste")
    def test_recusa_assinatura_adulterada(self):
        url = "https://media.lwksistemas.com.br/files/37302743000126/luiz_222/fotos/a.jpg"
        assinada = assinar_url_midia(url, ttl_seconds=600)
        adulterada = assinada[:-4] + "xxxx"
        self.assertFalse(verificar_assinatura_midia(adulterada))

    @patch("core.media_storage.MEDIA_API_TOKEN", "segredo-teste")
    @patch("core.media_storage.time.time", return_value=1_700_000_000)
    def test_recusa_expirada(self, _now):
        url = "https://media.lwksistemas.com.br/files/37302743000126/luiz_222/fotos/a.jpg"
        assinada = assinar_url_midia(url, ttl_seconds=60)
        with patch("core.media_storage.time.time", return_value=1_700_000_200):
            self.assertFalse(verificar_assinatura_midia(assinada))

    def test_ignora_url_externa(self):
        self.assertEqual(assinar_url_midia("https://evil.com/files/x/a.jpg"), "https://evil.com/files/x/a.jpg")


class TokenTenantTest(TestCase):
    @patch("core.media_storage.MEDIA_API_TOKEN", "master-token")
    def test_token_de_uma_loja_diferente_da_outra(self):
        felix = media_token_for_tenant("41449198000172")
        harmonis = media_token_for_tenant("37302743000126")
        self.assertNotEqual(felix, harmonis)
        self.assertNotEqual(felix, "master-token")
        self.assertEqual(len(felix), 64)

    @patch("core.media_storage.MEDIA_API_TOKEN", "master-token")
    @patch("core.media_storage.requests.post")
    def test_upload_envia_token_do_tenant(self, mock_post):
        from core.media_storage import media_upload_tenant

        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"url": "/files/37302743000126/admin/fotos/a.jpg", "size": 2},
        )
        media_upload_tenant("37302743000126", b"xx", filename="a.jpg", folder="admin/fotos")
        headers = mock_post.call_args.kwargs["headers"]
        esperado = media_token_for_tenant("37302743000126")
        self.assertEqual(headers["Authorization"], f"Bearer {esperado}")
        self.assertNotIn("master-token", headers["Authorization"])

    @patch("core.media_storage.MEDIA_API_TOKEN", "master-token")
    @patch("core.media_storage.requests.get")
    def test_listar_todas_as_lojas_usa_token_master(self, mock_get):
        from core.media_storage import media_list_tenants

        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"tenants": []})
        media_list_tenants()
        headers = mock_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer master-token")
