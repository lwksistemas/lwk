"""Backup da clínica: só administrador, dono ou superadmin. Caixa não leva o ZIP."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from superadmin.views.permissions import IsOwnerOrSuperAdmin


class _View:
    def __init__(self, action):
        self.action = action


class BackupPerfilClinicaTest(SimpleTestCase):
    def _loja(self):
        return SimpleNamespace(id=6, owner=SimpleNamespace(id=1))

    def _user(self):
        return SimpleNamespace(id=2, is_superuser=False, is_authenticated=True)

    def _permite(self, perfil, action="exportar_backup", vendedor=False):
        vinculo = SimpleNamespace(perfil=perfil) if perfil else None
        prof_qs = MagicMock()
        prof_qs.only.return_value.first.return_value = vinculo
        with (
            patch("superadmin.views.permissions.ProfissionalUsuario") as profissional,
            patch("superadmin.models.UsuarioSistema") as suporte,
            patch("superadmin.models.VendedorUsuario") as vendedor_model,
        ):
            profissional.PERFIL_ADMINISTRADOR = "administrador"
            profissional.objects.filter.return_value = prof_qs
            suporte.objects.filter.return_value.exists.return_value = False
            vendedor_model.objects.filter.return_value.exists.return_value = vendedor
            request = SimpleNamespace(user=self._user())
            return IsOwnerOrSuperAdmin().has_object_permission(
                request, _View(action), self._loja(),
            )

    def test_caixa_limpeza_estoque_e_profissional_nao_baixam(self):
        for perfil in ("caixa", "limpeza", "estoque", "profissional", "recepcionista"):
            self.assertFalse(self._permite(perfil), perfil)
            self.assertFalse(self._permite(perfil, action="importar_backup"), perfil)

    def test_administrador_baixa(self):
        self.assertTrue(self._permite("administrador"))

    def test_vendedor_do_crm_continua_podendo(self):
        self.assertTrue(self._permite(None, vendedor=True))
