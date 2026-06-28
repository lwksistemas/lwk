"""RBAC: limpeza bloqueada em cadastros; profissional com escopo na agenda."""
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from clinica_beleza.permissions import (
    appointment_in_agenda_scope,
    resolve_agenda_professional_scope,
)
from superadmin.models import ProfissionalUsuario


class AgendaScopeHelpersTest(SimpleTestCase):
    def test_owner_ve_agenda_completa(self):
        request = MagicMock()
        request.user = MagicMock(is_authenticated=True, id=1)
        loja = MagicMock(owner_id=1)
        with patch('clinica_beleza.permissions._loja_and_profissional', return_value=(loja, None)):
            self.assertIsNone(resolve_agenda_professional_scope(request))

    def test_profissional_escopo_proprio(self):
        request = MagicMock()
        request.user = MagicMock(is_authenticated=True, id=2)
        prof = MagicMock(perfil=ProfissionalUsuario.PERFIL_PROFISSIONAL, professional_id=42)
        loja = MagicMock(owner_id=99)
        with patch('clinica_beleza.permissions._loja_and_profissional', return_value=(loja, prof)):
            self.assertEqual(resolve_agenda_professional_scope(request), 42)

    def test_appointment_in_scope(self):
        appt = MagicMock(professional_id=42)
        self.assertTrue(appointment_in_agenda_scope(appt, None))
        self.assertTrue(appointment_in_agenda_scope(appt, 42))
        self.assertFalse(appointment_in_agenda_scope(appt, 7))


class LimpezaCadastros403Test(TestCase):
    """Perfil limpeza não acessa cadastros (CLINICA_RECEPCAO)."""

    def setUp(self):
        from superadmin.models import Loja, PlanoAssinatura, TipoLoja
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from superadmin.session_manager import SessionManager

        self.tipo = TipoLoja.objects.create(
            nome='Clínica da Beleza', slug='clinica-beleza', codigo='CLB',
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico', slug='basico', preco_mensal=99,
        )
        self.owner = User.objects.create_user('own@t.com', 'own@t.com', 'pass12345')
        self.loja = Loja.objects.create(
            nome='Test', slug='test-loja', cpf_cnpj='33333333000333',
            tipo_loja=self.tipo, plano=self.plano, owner=self.owner,
        )
        self.limpeza_user = User.objects.create_user('limp@t.com', 'limp@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=self.limpeza_user,
            loja=self.loja,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_LIMPEZA,
        )
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.limpeza_user).access_token)
        sid = SessionManager.create_session(self.limpeza_user.id, token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SESSION_ID=sid,
            HTTP_X_LOJA_ID=str(self.loja.id),
            HTTP_X_TENANT_SLUG=self.loja.slug,
        )
        self.headers = {}

    def _get(self, path):
        return self.client.get(
            path,
            HTTP_X_LOJA_ID=str(self.loja.id),
            HTTP_X_TENANT_SLUG=self.loja.slug,
        )

    def test_limpeza_negado_procedimentos(self):
        r = self._get('/api/clinica-beleza/procedures/')
        self.assertEqual(r.status_code, 403)

    def test_limpeza_negado_convenios(self):
        r = self._get('/api/clinica-beleza/convenios/')
        self.assertEqual(r.status_code, 403)

    def test_limpeza_negado_pacientes(self):
        r = self._get('/api/clinica-beleza/patients/')
        self.assertEqual(r.status_code, 403)

    def test_limpeza_negado_estoque_listagem(self):
        r = self._get('/api/clinica-beleza/estoque/')
        self.assertEqual(r.status_code, 403)


class ProfissionalAgendaAccessTest(TestCase):
    """Profissional acessa agenda (CLINICA_AGENDA) — não recebe 403 por permissão."""

    def setUp(self):
        from superadmin.models import Loja, PlanoAssinatura, TipoLoja
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from superadmin.session_manager import SessionManager

        self.tipo = TipoLoja.objects.create(
            nome='Clínica da Beleza', slug='clinica-beleza', codigo='CLB2',
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico', slug='basico2', preco_mensal=99,
        )
        self.owner = User.objects.create_user('own2@t.com', 'own2@t.com', 'pass12345')
        self.loja = Loja.objects.create(
            nome='Test2', slug='test-loja-2', cpf_cnpj='44444444000444',
            tipo_loja=self.tipo, plano=self.plano, owner=self.owner,
        )
        self.prof_user = User.objects.create_user('prof@t.com', 'prof@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=self.prof_user,
            loja=self.loja,
            professional_id=10,
            perfil=ProfissionalUsuario.PERFIL_PROFISSIONAL,
        )
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.prof_user).access_token)
        sid = SessionManager.create_session(self.prof_user.id, token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SESSION_ID=sid,
        )

    @patch('clinica_beleza.views_agenda._agenda_events_queryset')
    def test_profissional_pode_listar_agenda(self, mock_qs):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = []
        mock_qs.return_value = qs
        r = self.client.get(
            '/api/clinica-beleza/agenda/',
            HTTP_X_LOJA_ID=str(self.loja.id),
            HTTP_X_TENANT_SLUG=self.loja.slug,
        )
        self.assertNotEqual(r.status_code, 403)
