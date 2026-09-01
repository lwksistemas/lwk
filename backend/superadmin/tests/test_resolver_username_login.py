"""Login da loja aceita usuário ou e-mail."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from superadmin.services.login_service import resolver_username_para_login


class TestResolverUsernameParaLogin(SimpleTestCase):
    def test_vazio(self):
        self.assertEqual(resolver_username_para_login(""), "")
        self.assertEqual(resolver_username_para_login(None), "")

    @patch("django.contrib.auth.models.User")
    def test_username_existente(self, mock_user):
        mock_user.objects.filter.return_value.first.return_value = SimpleNamespace(username="marina")
        self.assertEqual(resolver_username_para_login("Marina"), "marina")

    @patch("django.contrib.auth.models.User")
    def test_email_da_loja_resolve_profissional(self, mock_user):
        mock_user.objects.filter.return_value.first.return_value = None
        loja = SimpleNamespace(owner=SimpleNamespace(email="nayarass03@hotmail.com", username="NAYARA"))
        pu = SimpleNamespace(user_id=10, user=SimpleNamespace(username="marina"))
        with patch(
            "superadmin.loja_utils.resolve_loja_by_slug_or_atalho",
            return_value=loja,
        ), patch(
            "superadmin.services.login_service.ProfissionalUsuario"
        ) as mock_pu, patch(
            "superadmin.services.login_service.VendedorUsuario"
        ):
            mock_pu.objects.filter.return_value.select_related.return_value.first.return_value = pu
            self.assertEqual(
                resolver_username_para_login("marina@clinicaharmonis.com.br", "clinicaharmonis"),
                "marina",
            )
