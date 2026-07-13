"""Queryset do relatório de comissão — filtros de empresa prestadora."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import SimpleTestCase

from crm_vendas.services_relatorio_comissao import queryset_oportunidades_comissao


class RelatorioComissaoQuerysetTest(SimpleTestCase):
    def _run(self, loja_id=1, empresa_id=10, vendedor_id=None):
        inicio, fim = date(2026, 6, 1), date(2026, 6, 30)
        chain = MagicMock()
        with patch("crm_vendas.models.Oportunidade") as mock_opp:
            mock_opp.objects.filter.return_value = chain
            chain.filter.return_value = chain
            chain.select_related.return_value = chain
            result = queryset_oportunidades_comissao(loja_id, empresa_id, vendedor_id, inicio, fim)
        return mock_opp, chain, result

    def test_filtra_loja_e_closed_won(self):
        mock_opp, chain, result = self._run()
        mock_opp.objects.filter.assert_called_once_with(loja_id=1, etapa="closed_won")
        chain.select_related.assert_called_once_with("lead", "lead__conta", "vendedor")
        self.assertIs(result, chain)

    def test_inclui_empresa_prestadora_ou_nula_no_filtro(self):
        _, chain, _ = self._run(empresa_id=42)
        empresa_q = chain.filter.call_args_list[0].args[0]
        self.assertIsInstance(empresa_q, Q)
        self.assertEqual(
            str(empresa_q),
            str(Q(empresa_prestadora_id=42) | Q(empresa_prestadora_id__isnull=True)),
        )

    def test_filtra_vendedor_quando_informado(self):
        with patch("crm_vendas.utils.get_vendedor_destino_merge_loja", return_value=None):
            _, chain, _ = self._run(vendedor_id=7)
        vendedor_call = chain.filter.call_args_list[-1]
        self.assertEqual(vendedor_call.kwargs, {"vendedor_id": 7})
