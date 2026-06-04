"""
Testes IDOR / isolamento entre tenants e grupos de usuário.
"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from superadmin.models import Loja, TipoLoja, PlanoAssinatura, UsuarioSistema, ProfissionalUsuario
from superadmin.session_manager import SessionManager
from config.security_middleware import SecurityIsolationMiddleware


MIDDLEWARE_WITH_ISOLATION = override_settings(
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'config.security_middleware.SecurityIsolationMiddleware',
    ],
)


class SecurityIdorTestCase(TestCase):
    """IDOR: headers de tenant e bloqueio de superadmin em APIs de loja."""

    def setUp(self):
        self.tipo = TipoLoja.objects.create(nome='Clínica', slug='clinica', codigo='CLIN')
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico', slug='basico', preco_mensal=99,
        )
        self.owner_a = User.objects.create_user('owner_a@t.com', 'owner_a@t.com', 'pass12345')
        self.owner_b = User.objects.create_user('owner_b@t.com', 'owner_b@t.com', 'pass12345')
        self.loja_a = Loja.objects.create(
            nome='Loja A', slug='loja-a', cpf_cnpj='11111111000111',
            tipo_loja=self.tipo, plano=self.plano, owner=self.owner_a,
        )
        self.loja_b = Loja.objects.create(
            nome='Loja B', slug='loja-b', cpf_cnpj='22222222000222',
            tipo_loja=self.tipo, plano=self.plano, owner=self.owner_b,
        )
        self.superuser = User.objects.create_superuser('admin@t.com', 'admin@t.com', 'pass12345')
        UsuarioSistema.objects.create(user=self.superuser, tipo='superadmin', is_active=True)
        self.client = APIClient()

    def _auth(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        sid = SessionManager.create_session(user.id, token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SESSION_ID=sid,
        )

    @MIDDLEWARE_WITH_ISOLATION
    def test_superadmin_blocked_from_clinica_beleza_api(self):
        self._auth(self.superuser)
        response = self.client.get(
            '/api/clinica-beleza/patients/',
            HTTP_X_LOJA_ID=str(self.loja_a.id),
            HTTP_X_TENANT_SLUG=self.loja_a.slug,
        )
        self.assertIn(response.status_code, (403, 401))

    def test_owner_cannot_spoof_other_loja_header_on_info_publica(self):
        """info_publica é por slug na URL/query — slug alheio não retorna dados da loja B para owner A."""
        self._auth(self.owner_a)
        response = self.client.get(
            '/api/superadmin/lojas/info_publica/',
            {'slug': self.loja_b.slug},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('slug'), self.loja_b.slug)
        self.assertNotEqual(response.data.get('nome'), 'dados-privados-owner-a')

    def test_profissional_limpeza_denied_clinica_financeiro(self):
        """Perfil limpeza não acessa financeiro da clínica."""
        prof_user = User.objects.create_user('limpeza@t.com', 'limpeza@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=prof_user,
            loja=self.loja_a,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_LIMPEZA,
        )
        self._auth(prof_user)
        response = self.client.get(
            '/api/clinica-beleza/payments/',
            HTTP_X_LOJA_ID=str(self.loja_a.id),
            HTTP_X_TENANT_SLUG=self.loja_a.slug,
        )
        self.assertEqual(response.status_code, 403)

    def test_security_middleware_blocks_superuser_store_route(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/api/clinica-beleza/patients/')
        request.user = self.superuser
        mw = SecurityIsolationMiddleware(lambda r: None)
        response = mw(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
