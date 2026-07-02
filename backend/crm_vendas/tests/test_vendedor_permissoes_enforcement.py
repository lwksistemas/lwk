"""Enforcement de permissões granulares CRM (Fase 29 / Fase 33)."""
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase
from rest_framework import status

from crm_vendas.vendedor_permissoes_service import verificar_permissao_crm_action


class VerificarPermissaoCrmActionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/crm-vendas/leads/')
        self.request.user = MagicMock()

    @patch('crm_vendas.utils.is_owner', return_value=True)
    def test_owner_sempre_permitido(self, _mock_owner):
        self.assertIsNone(verificar_permissao_crm_action(self.request, 'lead', 'list'))

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch('crm_vendas.vendedor_permissoes_service.permissoes_codenames_usuario_crm', return_value=[])
    def test_sem_permissoes_configuradas_mantem_legado(self, *_mocks):
        self.assertIsNone(verificar_permissao_crm_action(self.request, 'lead', 'list'))

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch(
        'crm_vendas.vendedor_permissoes_service.permissoes_codenames_usuario_crm',
        return_value=['view_lead'],
    )
    def test_vendedor_sem_perm_bloqueado(self, *_mocks):
        self.request.user.has_perm.return_value = False
        denied = verificar_permissao_crm_action(self.request, 'lead', 'list')
        self.assertIsNotNone(denied)
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch(
        'crm_vendas.vendedor_permissoes_service.permissoes_codenames_usuario_crm',
        return_value=['view_lead'],
    )
    def test_vendedor_com_has_perm_permitido(self, *_mocks):
        self.request.user.has_perm.return_value = True
        self.assertIsNone(verificar_permissao_crm_action(self.request, 'lead', 'list'))

    @patch('crm_vendas.utils.is_owner', return_value=False)
    @patch(
        'crm_vendas.vendedor_permissoes_service.permissoes_codenames_usuario_crm',
        return_value=['change_proposta'],
    )
    def test_destroy_mapeia_para_delete(self, *_mocks):
        self.request.user.has_perm.side_effect = lambda perm: perm.endswith('delete_proposta')
        self.assertIsNone(verificar_permissao_crm_action(self.request, 'proposta', 'destroy'))
