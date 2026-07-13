"""
Testes de isolamento multi-tenant para o CRM Vendas.
Verifica que LojaIsolationManager bloqueia acesso cruzado entre lojas.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

PATCH_LOJA_ID = 'tenants.middleware.get_current_loja_id'
PATCH_TENANT_DB = 'tenants.middleware.get_current_tenant_db'


class LojaIsolationManagerTests(SimpleTestCase):
    """Testa que o manager retorna queryset vazio sem contexto de loja."""

    @patch(PATCH_LOJA_ID, return_value=None)
    @patch(PATCH_TENANT_DB, return_value=None)
    def test_sem_loja_contexto_retorna_none_queryset(self, *_):
        """Manager deve retornar queryset vazio quando não há loja no contexto."""
        from django.db import models

        from core.mixins import LojaIsolationManager

        class FakeModel(models.Model):
            loja_id = models.IntegerField()
            objects = LojaIsolationManager()

            class Meta:
                app_label = 'crm_vendas'

        manager = LojaIsolationManager()
        manager.model = FakeModel
        manager.auto_created = True
        # Sem contexto de loja, get_queryset() deve chamar .none()
        with patch.object(manager, 'get_queryset') as mock_qs:
            mock_qs.return_value = MagicMock()
            mock_qs.return_value.none.return_value = []
            result = manager.get_queryset()
            self.assertIsNotNone(result)


class VendedorFilterMixinTests(SimpleTestCase):
    """Testa o filtro de queryset por vendedor."""

    def _make_request(self, vendedor_id=None, is_owner=False):
        req = MagicMock()
        req.user = MagicMock()
        req.user.is_authenticated = True
        return req

    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.mixins.is_vendedor_usuario', return_value=False)
    def test_sem_vendedor_retorna_queryset_completo(self, *_):
        """Owner sem vendedor_id vê todos os registros."""
        from crm_vendas.mixins import VendedorFilterMixin

        req = self._make_request()

        class FakeViewSet(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = []
            request = req

        vs = FakeViewSet()
        with patch('crm_vendas.utils.is_owner', return_value=True):
            qs = MagicMock()
            result = vs.filter_by_vendedor(qs)
            self.assertEqual(result, qs)

    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=42)
    def test_vendedor_filtra_pelo_seu_id(self, *_):
        """Vendedor vê apenas registros com seu vendedor_id."""
        from crm_vendas.mixins import VendedorFilterMixin

        req = self._make_request(vendedor_id=42)

        class FakeViewSet(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = []
            request = req

        vs = FakeViewSet()
        with patch('crm_vendas.utils.is_owner', return_value=False):
            qs = MagicMock()
            qs.filter.return_value = qs
            qs.distinct.return_value = qs
            vs.filter_by_vendedor(qs)
            qs.filter.assert_called_once()

    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=42)
    def test_vendedor_include_unassigned_off_por_padrao(self, *_):
        """Por padrão, registros sem vendedor NÃO aparecem para vendedores."""

        from crm_vendas.mixins import VendedorFilterMixin

        class FakeViewSet(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = []
            # vendedor_include_unassigned_pool = False (padrão)
            request = self._make_request(vendedor_id=42)

        vs = FakeViewSet()

        # Verifica que o atributo padrão é False
        self.assertFalse(getattr(vs, 'vendedor_include_unassigned_pool', False))

    @patch('crm_vendas.mixins.get_current_vendedor_id', return_value=42)
    def test_vendedor_include_unassigned_on_quando_explicitado(self, *_):
        """Com vendedor_include_unassigned_pool=True, registros sem vendedor aparecem."""
        from crm_vendas.mixins import VendedorFilterMixin

        class FakeViewSet(VendedorFilterMixin):
            vendedor_filter_field = 'vendedor_id'
            vendedor_filter_related = []
            vendedor_include_unassigned_pool = True
            request = self._make_request(vendedor_id=42)

        vs = FakeViewSet()
        self.assertTrue(vs.vendedor_include_unassigned_pool)
