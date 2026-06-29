"""RBAC: config NFS-e restrita a owner/administrador (CLINICA_ADMIN)."""
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from superadmin.authentication import invalidate_session_cache
from superadmin.models import Loja, PlanoAssinatura, ProfissionalUsuario, TipoLoja
from superadmin.session_manager import SessionManager

NFSE_CONFIG_URL = '/api/clinica-beleza/nfse-config/'
NFSE_TEST_URL = '/api/clinica-beleza/nfse-config/test-issnet/'


class _NFSeRBACBase(TestCase):
    def _create_loja(self, *, slug_suffix: str) -> Loja:
        tipo = TipoLoja.objects.create(
            nome='Clínica da Beleza',
            slug=f'clb-nfse-{slug_suffix}',
            codigo=f'N{slug_suffix[:3]}',
        )
        plano = PlanoAssinatura.objects.create(
            nome='Básico',
            slug=f'basico-nfse-{slug_suffix}',
            preco_mensal=99,
        )
        owner = User.objects.create_user(
            f'owner-nfse-{slug_suffix}@t.com',
            f'owner-nfse-{slug_suffix}@t.com',
            'pass12345',
        )
        return Loja.objects.create(
            nome='NFSe RBAC',
            slug=f'nfse-rbac-{slug_suffix}',
            cpf_cnpj=f'88888888{slug_suffix[:6]}',
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
        )

    def _client_for_user(self, user: User, loja: Loja) -> APIClient:
        invalidate_session_cache(user.id)
        client = APIClient()
        token = str(RefreshToken.for_user(user).access_token)
        sid = SessionManager.create_session(user.id, token)
        client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SESSION_ID=sid,
            HTTP_X_LOJA_ID=str(loja.id),
            HTTP_X_TENANT_SLUG=loja.slug,
        )
        return client


class NFSeConfigForbiddenTest(_NFSeRBACBase):
    def setUp(self):
        self.loja = self._create_loja(slug_suffix='forbidden')

        self.recepcionista = User.objects.create_user('rec-nfse@t.com', 'rec-nfse@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=self.recepcionista,
            loja=self.loja,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        )
        self.recepcionista_client = self._client_for_user(self.recepcionista, self.loja)

        self.profissional = User.objects.create_user('prof-nfse@t.com', 'prof-nfse@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=self.profissional,
            loja=self.loja,
            professional_id=2,
            perfil=ProfissionalUsuario.PERFIL_PROFISSIONAL,
        )
        self.profissional_client = self._client_for_user(self.profissional, self.loja)

    def test_recepcionista_negado_get_nfse_config(self):
        response = self.recepcionista_client.get(NFSE_CONFIG_URL)
        self.assertEqual(response.status_code, 403)

    def test_profissional_negado_get_nfse_config(self):
        response = self.profissional_client.get(NFSE_CONFIG_URL)
        self.assertEqual(response.status_code, 403)

    def test_profissional_negado_patch_nfse_config(self):
        response = self.profissional_client.patch(NFSE_CONFIG_URL, {'provedor': 'asaas'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_recepcionista_negado_test_issnet(self):
        response = self.recepcionista_client.post(NFSE_TEST_URL, {}, format='json')
        self.assertEqual(response.status_code, 403)


class NFSeConfigAllowedTest(_NFSeRBACBase):
    @patch('clinica_beleza.views_nfse_config.ClinicaBelezaNFSeConfigSerializer')
    @patch('clinica_beleza.views_nfse_config.get_or_create_nfse_config')
    def test_administrador_pode_ler_nfse_config(self, mock_get_config, mock_serializer_cls):
        loja = self._create_loja(slug_suffix='admin')
        admin = User.objects.create_user('admin-nfse@t.com', 'admin-nfse@t.com', 'pass12345')
        ProfissionalUsuario.objects.create(
            user=admin,
            loja=loja,
            professional_id=3,
            perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
        )
        mock_get_config.return_value = MagicMock(loja_id=loja.id)
        mock_serializer_cls.return_value.data = {'provedor_nf': 'asaas'}

        client = self._client_for_user(admin, loja)
        response = client.get(NFSE_CONFIG_URL)
        self.assertEqual(response.status_code, 200)

    @patch('clinica_beleza.views_nfse_config.ClinicaBelezaNFSeConfigSerializer')
    @patch('clinica_beleza.views_nfse_config.get_or_create_nfse_config')
    def test_owner_pode_ler_nfse_config(self, mock_get_config, mock_serializer_cls):
        loja = self._create_loja(slug_suffix='owner')
        mock_get_config.return_value = MagicMock(loja_id=loja.id)
        mock_serializer_cls.return_value.data = {'provedor_nf': 'asaas'}

        client = self._client_for_user(loja.owner, loja)
        response = client.get(NFSE_CONFIG_URL)
        self.assertEqual(response.status_code, 200)
