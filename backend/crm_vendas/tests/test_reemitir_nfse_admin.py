"""A reemissão da nota de comissão fica com o administrador do CRM."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from crm_vendas.views_relatorio_comissao_admin import reemitir_nfse_view


class ReemitirNfseAdminTests(SimpleTestCase):
    @patch("crm_vendas.services_relatorio_comissao.processar_pagamento_comissao")
    @patch("crm_vendas.utils.usuario_administra_crm", return_value=False)
    def test_vendedor_comum_nao_reemite(self, _admin, emitir):
        request = APIRequestFactory().post("/crm-vendas/relatorios-comissao/1/reemitir-nfse/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_superuser=False, pk=1, id=1))
        response = reemitir_nfse_view(request, 1)
        self.assertEqual(response.status_code, 403)
        self.assertIn("administrador", response.data["detail"])
        emitir.assert_not_called()
