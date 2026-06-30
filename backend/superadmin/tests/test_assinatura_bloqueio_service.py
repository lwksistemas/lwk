"""Testes do bloqueio por inadimplência de assinatura."""
from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from superadmin.services.assinatura_bloqueio_service import (
    DAYS_TO_BLOCK,
    aplicar_bloqueio_inadimplencia_loja,
    check_inadimplencia_block,
    dias_atraso_assinatura,
    loja_deve_estar_bloqueada,
    path_allowed_when_store_blocked,
)

User = get_user_model()


class TestPathAllowedWhenBlocked(TestCase):
    def test_heartbeat_permitido(self):
        self.assertTrue(path_allowed_when_store_blocked('/api/superadmin/lojas/heartbeat/'))
        self.assertTrue(path_allowed_when_store_blocked('/api/superadmin/lojas/heartbeat'))

    def test_financeiro_permitido(self):
        self.assertTrue(path_allowed_when_store_blocked('/api/superadmin/loja/vendasbeta/financeiro/'))
        self.assertTrue(path_allowed_when_store_blocked('/api/superadmin/loja-financeiro/1/'))
        self.assertTrue(path_allowed_when_store_blocked('/api/superadmin/loja-pagamentos/99/baixar_boleto_pdf/'))

    def test_crm_bloqueado(self):
        self.assertFalse(path_allowed_when_store_blocked('/api/crm-vendas/leads/'))


class TestDiasAtrasoAssinatura(TestCase):
    def test_sem_atraso(self):
        loja = Mock()
        loja.financeiro.data_proxima_cobranca = date.today() + timedelta(days=5)
        with patch('superadmin.models.PagamentoLoja') as mock_pg:
            mock_pg.objects.filter.return_value.order_by.return_value.first.return_value = None
            self.assertEqual(dias_atraso_assinatura(loja), 0)

    def test_atraso_pela_data_proxima_cobranca(self):
        loja = Mock()
        loja.financeiro.data_proxima_cobranca = date.today() - timedelta(days=7)
        with patch('superadmin.models.PagamentoLoja') as mock_pg:
            mock_pg.objects.filter.return_value.order_by.return_value.first.return_value = None
            self.assertEqual(dias_atraso_assinatura(loja), 7)
            self.assertTrue(loja_deve_estar_bloqueada(loja))


class TestAplicarBloqueio(TestCase):
    def test_bloqueia_apos_cinco_dias(self):
        loja = Mock()
        loja.id = 1
        loja.slug = 'vendasbeta'
        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ''
        loja.days_overdue = 0
        financeiro = Mock()
        financeiro.status_pagamento = 'pendente'
        loja.financeiro = financeiro

        with patch(
            'superadmin.services.assinatura_bloqueio_service.dias_atraso_assinatura',
            return_value=DAYS_TO_BLOCK,
        ):
            out = aplicar_bloqueio_inadimplencia_loja(loja, persistir=False)

        self.assertTrue(out['blocked'])
        self.assertTrue(loja.is_blocked)
        self.assertEqual(financeiro.status_pagamento, 'suspenso')


class TestCheckInadimplenciaBlock(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock(is_authenticated=True, is_superuser=False, username='owner')

    @patch('core.store_membership.resolve_loja_for_user')
    @patch('core.store_membership.user_belongs_to_store', return_value=True)
    def test_retorna_403_quando_bloqueada(self, _belongs, mock_resolve):
        loja = Mock(slug='vendasbeta', is_blocked=True)
        mock_resolve.return_value = loja
        request = self.factory.get('/api/crm-vendas/leads/')
        request.user = self.user
        request.headers = {'X-Tenant-Slug': 'vendasbeta'}

        response = check_inadimplencia_block(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)

    @patch('core.store_membership.resolve_loja_for_user')
    @patch('core.store_membership.user_belongs_to_store', return_value=True)
    def test_financeiro_liberado(self, _belongs, mock_resolve):
        loja = Mock(slug='vendasbeta', is_blocked=True)
        mock_resolve.return_value = loja
        request = self.factory.get('/api/superadmin/loja/vendasbeta/financeiro/')
        request.user = self.user

        self.assertIsNone(check_inadimplencia_block(request))
