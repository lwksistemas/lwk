from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from core.store_membership import user_belongs_to_store


class StoreMembershipTests(SimpleTestCase):
    @patch('core.store_membership.funcionario_email_ativo_na_loja')
    @patch('superadmin.models.VendedorUsuario')
    @patch('superadmin.models.ProfissionalUsuario')
    @patch('tenants.middleware.resolve_loja_from_slug_or_cnpj')
    def test_owner_belongs(self, mock_resolve, _pu, _vu, _func):
        loja = MagicMock(is_active=True, owner_id=10, id=1)
        mock_resolve.return_value = loja
        user = MagicMock(is_authenticated=True, id=10)
        self.assertTrue(user_belongs_to_store(user, 'minha-loja'))

    @patch('core.store_membership.funcionario_email_ativo_na_loja', return_value=True)
    @patch('superadmin.models.VendedorUsuario')
    @patch('superadmin.models.ProfissionalUsuario')
    @patch('tenants.middleware.resolve_loja_from_slug_or_cnpj')
    def test_funcionario_email_belongs(self, mock_resolve, mock_pu, mock_vu, _func):
        loja = MagicMock(is_active=True, owner_id=99, id=1)
        mock_resolve.return_value = loja
        mock_pu.objects.filter.return_value.exists.return_value = False
        mock_vu.objects.filter.return_value.exists.return_value = False
        user = MagicMock(is_authenticated=True, id=5)
        self.assertTrue(user_belongs_to_store(user, 'hotel-x'))

    def test_unauthenticated_false(self):
        user = MagicMock(is_authenticated=False)
        self.assertFalse(user_belongs_to_store(user, 'x'))
