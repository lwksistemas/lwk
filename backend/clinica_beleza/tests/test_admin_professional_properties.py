"""Property-style tests para admin como profissional (toggle idempotente)."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.admin_professional_service import (
    desabilitar_admin_como_profissional,
    habilitar_admin_como_profissional,
    obter_status_admin_profissional,
)


class AdminProfessionalPropertyTest(TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.email = "admin@test.com"
        self.user.get_full_name.return_value = "Admin Teste"
        self.user.username = "admin"

    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    def test_desabilitar_duas_vezes_mantem_inativo(self, mock_get):
        """Property: desabilitar repetido é idempotente (is_active=False)."""
        prof = MagicMock(is_active=True, is_profissional=True)
        mock_get.return_value = prof
        for _ in range(3):
            desabilitar_admin_como_profissional(1, self.user)
        self.assertFalse(prof.is_active)
        prof.save.assert_called_once()

    @patch("superadmin.models.Loja")
    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    @patch("clinica_beleza.admin_professional_service.Professional")
    def test_habilitar_duas_vezes_retorna_mesmo_profissional(self, mock_prof_cls, mock_get_prof, mock_loja_cls):
        """Property: habilitar repetido é idempotente (reativa, não duplica)."""
        loja = MagicMock(id=1, owner=self.user, owner_telefone="")
        loja.owner.email = "admin@test.com"
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja

        prof = MagicMock(id=9, is_active=False, is_profissional=False, nome="")
        mock_get_prof.return_value = prof

        r1 = habilitar_admin_como_profissional(1, self.user)
        r2 = habilitar_admin_como_profissional(1, self.user)
        self.assertEqual(r1.id, r2.id)
        mock_prof_cls.objects.create.assert_not_called()

    @patch("clinica_beleza.admin_professional_service._profissional_do_owner")
    def test_status_reflete_is_active_e_is_profissional(self, mock_get):
        """Property: is_enabled = is_active AND is_profissional != False."""
        cases = [
            (True, True, True),
            (True, False, False),
            (False, True, False),
            (False, False, False),
        ]
        for is_active, is_prof, expected in cases:
            with self.subTest(is_active=is_active, is_prof=is_prof):
                prof = MagicMock(id=1, is_active=is_active, is_profissional=is_prof)
                mock_get.return_value = prof
                data = obter_status_admin_profissional(1, self.user)
                self.assertEqual(data["is_enabled"], expected)
