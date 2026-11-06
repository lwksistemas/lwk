"""Backup da clínica: só administrador, dono ou superadmin. Caixa não leva o ZIP."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from superadmin.views.permissions import IsOwnerOrSuperAdmin, _vendedor_crm_e_admin
from tenants.middleware import get_current_loja_id, get_current_tenant_db, set_current_loja_id, set_current_tenant_db


class _View:
    def __init__(self, action):
        self.action = action


class BackupPerfilClinicaTest(SimpleTestCase):
    def _loja(self):
        return SimpleNamespace(id=6, owner=SimpleNamespace(id=1))

    def _user(self):
        return SimpleNamespace(id=2, is_superuser=False, is_authenticated=True)

    def _permite(self, perfil, action="exportar_backup", vendedor_admin=False):
        vinculo = SimpleNamespace(perfil=perfil) if perfil else None
        prof_qs = MagicMock()
        prof_qs.only.return_value.first.return_value = vinculo
        with (
            patch("superadmin.views.permissions.ProfissionalUsuario") as profissional,
            patch("superadmin.models.UsuarioSistema") as suporte,
            patch("superadmin.views.permissions._vendedor_crm_e_admin", return_value=vendedor_admin),
        ):
            profissional.PERFIL_ADMINISTRADOR = "administrador"
            profissional.objects.filter.return_value = prof_qs
            suporte.objects.filter.return_value.exists.return_value = False
            request = SimpleNamespace(user=self._user())
            return IsOwnerOrSuperAdmin().has_object_permission(
                request, _View(action), self._loja(),
            )

    def test_caixa_limpeza_estoque_e_profissional_nao_baixam(self):
        for perfil in ("caixa", "limpeza", "estoque", "profissional", "recepcionista"):
            self.assertFalse(self._permite(perfil), perfil)
            self.assertFalse(self._permite(perfil, action="importar_backup"), perfil)

    def test_administrador_exporta_e_nao_importa(self):
        self.assertTrue(self._permite("administrador"))
        self.assertFalse(self._permite("administrador", action="importar_backup"))

    def test_vendedor_comum_nao_leva_o_zip(self):
        self.assertFalse(self._permite(None))
        self.assertFalse(self._permite(None, action="importar_backup"))

    def test_vendedor_administrador_exporta_e_importa(self):
        self.assertTrue(self._permite(None, vendedor_admin=True))
        self.assertTrue(self._permite(None, action="importar_backup", vendedor_admin=True))


class VendedorAdminDoBackupTest(SimpleTestCase):
    def _consulta(self, vinculo, vendedor=None, erro=None):
        qs_vinculo = MagicMock()
        qs_vinculo.only.return_value.first.return_value = vinculo
        qs_vendedor = MagicMock()
        qs_vendedor.only.return_value.first.return_value = vendedor
        loja = SimpleNamespace(id=4, database_name="loja_felix")
        set_current_tenant_db("antes")
        set_current_loja_id(99)
        banco_patch = (
            patch("core.db_config.ensure_loja_database_config", side_effect=erro)
            if erro else
            patch("core.db_config.ensure_loja_database_config", return_value=True)
        )
        with (
            patch("superadmin.models.VendedorUsuario") as acesso,
            banco_patch as banco,
            patch("crm_vendas.models.Vendedor") as modelo,
        ):
            acesso.objects.filter.return_value = qs_vinculo
            modelo.objects.filter.return_value = qs_vendedor
            permitido = _vendedor_crm_e_admin(SimpleNamespace(id=2), loja)
        self.assertEqual(get_current_tenant_db(), "antes")
        self.assertEqual(get_current_loja_id(), 99)
        return permitido, banco

    def test_so_o_administrador(self):
        permitido, banco = self._consulta(None)
        self.assertFalse(permitido)
        banco.assert_not_called()

        permitido, _banco = self._consulta(SimpleNamespace(vendedor_id=3), SimpleNamespace(is_admin=False))
        self.assertFalse(permitido)

        permitido, _banco = self._consulta(SimpleNamespace(vendedor_id=3), SimpleNamespace(is_admin=True))
        self.assertTrue(permitido)

    def test_falha_na_leitura_nega(self):
        permitido, _banco = self._consulta(
            SimpleNamespace(vendedor_id=3), erro=RuntimeError("banco"),
        )
        self.assertFalse(permitido)
