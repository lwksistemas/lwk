"""A aparência do login do sistema não fica aberta para a loja."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from superadmin.views.permissions import IsSuperAdminOuSuporte


class LoginConfigPermissaoTests(SimpleTestCase):
    def _permite(self, user, suporte=False):
        qs = MagicMock()
        qs.exists.return_value = suporte
        with patch("superadmin.models.UsuarioSistema.objects.filter", return_value=qs):
            return IsSuperAdminOuSuporte().has_permission(SimpleNamespace(user=user), None)

    def test_loja_comum_nao_altera(self):
        user = SimpleNamespace(is_authenticated=True, is_superuser=False)
        self.assertFalse(self._permite(user))

    def test_superadmin_e_suporte_alteram(self):
        superadmin = SimpleNamespace(is_authenticated=True, is_superuser=True)
        suporte = SimpleNamespace(is_authenticated=True, is_superuser=False)
        self.assertTrue(self._permite(superadmin))
        self.assertTrue(self._permite(suporte, suporte=True))
