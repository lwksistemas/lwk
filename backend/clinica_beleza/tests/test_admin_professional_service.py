"""Testes do service admin como profissional."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.admin_professional_service import (
    desabilitar_admin_como_profissional,
    habilitar_admin_como_profissional,
    obter_status_admin_profissional,
)


class AdminProfessionalServiceTest(TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.email = "admin@test.com"
        self.user.get_full_name.return_value = "Admin Teste"
        self.user.username = "admin"

    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    def test_obter_status_habilitado(self, mock_get):
        prof = MagicMock(id=5, is_active=True, is_profissional=True)
        mock_get.return_value = prof
        data = obter_status_admin_profissional(1, self.user)
        self.assertTrue(data["is_enabled"])
        self.assertEqual(data["professional_id"], 5)

    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    def test_obter_status_desabilitado(self, mock_get):
        mock_get.return_value = None
        data = obter_status_admin_profissional(1, self.user)
        self.assertFalse(data["is_enabled"])

    @patch("superadmin.models.Loja")
    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    @patch("clinica_beleza.admin_professional_service.Professional")
    def test_habilitar_reativa_existente(self, mock_prof_cls, mock_get_prof, mock_loja_cls):
        loja = MagicMock(id=1, owner=self.user, owner_telefone="")
        loja.owner.email = "admin@test.com"
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja

        prof = MagicMock(id=9, is_active=False, is_profissional=False, nome="")
        mock_get_prof.return_value = prof

        result = habilitar_admin_como_profissional(1, self.user)
        self.assertEqual(result.id, 9)
        prof.save.assert_called_once()

    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    def test_desabilitar_idempotente(self, mock_get):
        prof = MagicMock(is_active=True)
        mock_get.return_value = prof
        desabilitar_admin_como_profissional(1, self.user)
        self.assertFalse(prof.is_active)
        prof.save.assert_called_once()
