"""Validações da view financeiro PDF do CRM."""
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from crm_vendas.views_financeiro import financeiro_crm_relatorio_pdf


class FinanceiroCrmRelatorioPdfViewTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("tenants.middleware.get_current_loja_id", return_value=None)
    @patch("crm_vendas.views_financeiro.get_current_loja_id", return_value=None)
    def test_sem_loja_retorna_400(self, _view_loja, _mw_loja):
        request = self.factory.post("/api/crm-vendas/financeiro/relatorio-pdf/", {}, format="json")
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 400)

    @patch("crm_vendas.views_financeiro.get_current_loja_id", return_value=4)
    def test_periodo_personalizado_sem_datas_400(self, _loja):
        request = self.factory.post(
            "/api/crm-vendas/financeiro/relatorio-pdf/",
            {"periodo": "personalizado"},
            format="json",
        )
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 400)

    @patch("crm_vendas.relatorios_financeiro.gerar_relatorio_financeiro_vendedor")
    @patch("crm_vendas.views_financeiro.is_owner", return_value=True)
    @patch("crm_vendas.views_financeiro.get_current_vendedor_id", return_value=None)
    @patch("crm_vendas.views_financeiro.get_current_loja_id", return_value=4)
    def test_gera_pdf_com_sucesso(self, _loja, _vend, _owner, mock_gerar):
        buf = BytesIO(b"%PDF-fake")
        mock_gerar.return_value = buf
        request = self.factory.post(
            "/api/crm-vendas/financeiro/relatorio-pdf/",
            {"periodo": "mes_atual"},
            format="json",
        )
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
