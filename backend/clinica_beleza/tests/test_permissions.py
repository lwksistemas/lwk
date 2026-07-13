"""Testes unitários para as permissões RBAC da Clínica da Beleza.
Cobre todos os perfis × todas as classes de permissão.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.permissions import (
    IsAgendaOrAdmin,
    IsClinicaAdmin,
    IsClinicaEstoque,
    IsClinicaFinanceiro,
    IsClinicaLojaMember,
    IsClinicalOrEstoqueStaff,
    IsRecepcaoOrAdmin,
    appointment_in_agenda_scope,
    resolve_agenda_professional_scope,
)


def _make_request(user=None, authenticated=True):
    """Cria request mock com user."""
    request = MagicMock()
    if user is None:
        user = MagicMock()
    user.is_authenticated = authenticated
    request.user = user
    return request


def _make_loja(owner_id=1):
    loja = MagicMock()
    loja.owner_id = owner_id
    loja.id = 99
    return loja


def _make_prof(perfil="profissional", professional_id=10):
    prof = MagicMock()
    prof.perfil = perfil
    prof.professional_id = professional_id
    return prof


PATCH_TARGET = "clinica_beleza.permissions._loja_and_profissional"


class IsClinicaLojaMemberTests(SimpleTestCase):
    """IsClinicaLojaMember: owner ou qualquer profissional vinculado."""

    def setUp(self):
        self.perm = IsClinicaLojaMember()

    def test_unauthenticated_denied(self):
        request = _make_request(authenticated=False)
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_superuser_allowed(self, mock_lp):
        mock_lp.return_value = (None, "superuser")
        request = _make_request()
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_owner_allowed(self, mock_lp):
        loja = _make_loja(owner_id=5)
        mock_lp.return_value = (loja, None)
        request = _make_request()
        request.user.id = 5
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_profissional_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_no_loja_denied(self, mock_lp):
        mock_lp.return_value = (None, None)
        request = _make_request()
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_loja_but_no_prof_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, None)
        request = _make_request()
        request.user.id = 999  # not owner
        self.assertFalse(self.perm.has_permission(request, None))


class IsRecepcaoOrAdminTests(SimpleTestCase):
    """IsRecepcaoOrAdmin: owner, admin, recepcao, recepcionista."""

    def setUp(self):
        self.perm = IsRecepcaoOrAdmin()

    @patch(PATCH_TARGET)
    def test_owner_allowed(self, mock_lp):
        loja = _make_loja(owner_id=5)
        mock_lp.return_value = (loja, None)
        request = _make_request()
        request.user.id = 5
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_administrador_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("administrador"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_recepcao_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("recepcao"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_recepcionista_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("recepcionista"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_profissional_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_caixa_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("caixa"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_limpeza_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("limpeza"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_estoque_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("estoque"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class IsClinicaAdminTests(SimpleTestCase):
    """IsClinicaAdmin: owner ou administrador."""

    def setUp(self):
        self.perm = IsClinicaAdmin()

    @patch(PATCH_TARGET)
    def test_owner_allowed(self, mock_lp):
        loja = _make_loja(owner_id=5)
        mock_lp.return_value = (loja, None)
        request = _make_request()
        request.user.id = 5
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_administrador_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("administrador"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_recepcionista_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("recepcionista"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_profissional_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class IsAgendaOrAdminTests(SimpleTestCase):
    """IsAgendaOrAdmin: owner, admin, recepcao, recepcionista, profissional."""

    def setUp(self):
        self.perm = IsAgendaOrAdmin()

    @patch(PATCH_TARGET)
    def test_profissional_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_caixa_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("caixa"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_limpeza_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("limpeza"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class IsClinicaFinanceiroTests(SimpleTestCase):
    """IsClinicaFinanceiro: admin, recepcao, recepcionista, caixa."""

    def setUp(self):
        self.perm = IsClinicaFinanceiro()

    @patch(PATCH_TARGET)
    def test_caixa_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("caixa"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_profissional_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_estoque_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("estoque"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_limpeza_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("limpeza"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class IsClinicaEstoqueTests(SimpleTestCase):
    """IsClinicaEstoque: admin, recepcao, recepcionista, estoque."""

    def setUp(self):
        self.perm = IsClinicaEstoque()

    @patch(PATCH_TARGET)
    def test_estoque_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("estoque"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_profissional_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_caixa_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("caixa"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class IsClinicalOrEstoqueStaffTests(SimpleTestCase):
    """IsClinicalOrEstoqueStaff: admin, profissional, recepcao, recepcionista, estoque."""

    def setUp(self):
        self.perm = IsClinicalOrEstoqueStaff()

    @patch(PATCH_TARGET)
    def test_profissional_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_estoque_allowed(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("estoque"))
        request = _make_request()
        request.user.id = 99
        self.assertTrue(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_caixa_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("caixa"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))

    @patch(PATCH_TARGET)
    def test_limpeza_denied(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("limpeza"))
        request = _make_request()
        request.user.id = 99
        self.assertFalse(self.perm.has_permission(request, None))


class AgendaScopeTests(SimpleTestCase):
    """resolve_agenda_professional_scope e appointment_in_agenda_scope."""

    @patch(PATCH_TARGET)
    def test_owner_gets_full_scope(self, mock_lp):
        loja = _make_loja(owner_id=5)
        mock_lp.return_value = (loja, None)
        request = _make_request()
        request.user.id = 5
        self.assertIsNone(resolve_agenda_professional_scope(request))

    @patch(PATCH_TARGET)
    def test_profissional_gets_scoped(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("profissional", professional_id=42))
        request = _make_request()
        request.user.id = 99
        self.assertEqual(resolve_agenda_professional_scope(request), 42)

    @patch(PATCH_TARGET)
    def test_recepcionista_gets_full_scope(self, mock_lp):
        loja = _make_loja(owner_id=1)
        mock_lp.return_value = (loja, _make_prof("recepcionista"))
        request = _make_request()
        request.user.id = 99
        self.assertIsNone(resolve_agenda_professional_scope(request))

    def test_appointment_in_scope_none(self):
        """None scope = visão completa."""
        appt = MagicMock(professional_id=10)
        self.assertTrue(appointment_in_agenda_scope(appt, None))

    def test_appointment_in_scope_matches(self):
        appt = MagicMock(professional_id=42)
        self.assertTrue(appointment_in_agenda_scope(appt, 42))

    def test_appointment_not_in_scope(self):
        appt = MagicMock(professional_id=10)
        self.assertFalse(appointment_in_agenda_scope(appt, 42))
