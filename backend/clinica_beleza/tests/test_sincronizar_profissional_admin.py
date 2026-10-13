"""Edição no superadmin atualiza o profissional no schema da clínica."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.admin_professional_service import sincronizar_profissional_admin_owner


class SincronizarProfissionalAdminTests(SimpleTestCase):
    @patch("core.db_config.ensure_loja_database_config", return_value=True)
    @patch("superadmin.models.ProfissionalUsuario")
    @patch("clinica_beleza.admin_professional_service.Professional")
    def test_grava_email_novo_sem_contexto_da_loja(self, professional_model, vinculo_model, _ensure):
        owner = SimpleNamespace(
            get_full_name=lambda: "Ana Costa",
            username="ana",
            email="novo@exemplo.com",
        )
        loja = SimpleNamespace(
            id=3,
            database_name="loja_teste",
            database_created=True,
            owner_telefone="11999999999",
            owner=owner,
        )
        vinculo_model.objects.using.return_value.filter.return_value.first.return_value = SimpleNamespace(
            professional_id=8,
        )
        consulta = MagicMock()
        consulta.update.return_value = 1
        professional_model.objects.all_without_filter.return_value.using.return_value.filter.return_value = consulta

        ok = sincronizar_profissional_admin_owner(loja, owner)

        self.assertTrue(ok)
        professional_model.objects.all_without_filter.assert_called_once()
        consulta.update.assert_called_once_with(
            nome="Ana Costa",
            email="novo@exemplo.com",
            telefone="11999999999",
        )
