"""Edição no superadmin atualiza o vendedor no schema da loja."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.vendedor_admin_service import sincronizar_vendedor_admin_owner


class SincronizarVendedorAdminTests(SimpleTestCase):
    @patch("core.db_config.ensure_loja_database_config", return_value=True)
    @patch("superadmin.models.VendedorUsuario")
    @patch("crm_vendas.models.Vendedor")
    def test_grava_email_novo_sem_contexto_da_loja(self, vendedor_model, vinculo_model, _ensure):
        owner = SimpleNamespace(
            get_full_name=lambda: "Felipe Costa Felix",
            username="lhfd",
            email="novo@exemplo.com",
        )
        loja = SimpleNamespace(
            id=9,
            database_name="loja_teste",
            database_created=True,
            owner_telefone="",
            owner=owner,
        )
        vinculo_model.objects.using.return_value.filter.return_value.first.return_value = SimpleNamespace(
            vendedor_id=4,
        )
        consulta = MagicMock()
        consulta.update.return_value = 1
        vendedor_model.objects.all_without_filter.return_value.using.return_value.filter.return_value = consulta

        ok = sincronizar_vendedor_admin_owner(loja, owner)

        self.assertTrue(ok)
        vendedor_model.objects.all_without_filter.assert_called_once()
        consulta.update.assert_called_once_with(
            nome="Felipe Costa Felix",
            email="novo@exemplo.com",
            telefone="",
        )
