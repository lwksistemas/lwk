"""Filtro de atividades por vendedor no pipeline (calendário)."""
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import RequestFactory, SimpleTestCase

from crm_vendas.views_pipelines import AtividadeViewSet


class AtividadeVendedorFilterTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = AtividadeViewSet()
        self.view.request = self.factory.get('/crm-vendas/atividades/')

    @patch('crm_vendas.views_pipelines.get_current_vendedor_id', return_value=None)
    def test_sem_vendedor_retorna_queryset_intacto(self, _mock_vid):
        qs = MagicMock()
        result = self.view.filter_by_vendedor(qs)
        self.assertIs(result, qs)
        qs.filter.assert_not_called()

    @patch('crm_vendas.views_pipelines.get_current_vendedor_id', return_value=7)
    def test_com_vendedor_aplica_filtro_or_distinct(self, _mock_vid):
        qs = MagicMock()
        filtered = MagicMock()
        qs.filter.return_value.distinct.return_value = filtered

        result = self.view.filter_by_vendedor(qs)

        qs.filter.assert_called_once()
        q_arg = qs.filter.call_args.args[0]
        self.assertIsInstance(q_arg, Q)
        qs.filter.return_value.distinct.assert_called_once()
        self.assertIs(result, filtered)
