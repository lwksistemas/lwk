from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from crm_vendas.nome_arquivo import nome_arquivo_download
from crm_vendas.views_relatorio_comissao_public import motivo_link_comissao_encerrado

from .test_api_crm_integration import _CrmApiTestBase


class NomeArquivoDownloadTests(SimpleTestCase):
    def test_titulo_com_aspas_nao_entra_no_cabecalho(self):
        nome = nome_arquivo_download("proposta", 12, 'ACME"\r\n.pdf', extensao="pdf")
        self.assertNotIn('"', nome)
        self.assertNotIn("\n", nome)
        self.assertNotIn("\r", nome)
        self.assertTrue(nome.endswith(".pdf"))


class LinkComissaoTests(SimpleTestCase):
    def test_empresa_ainda_aberta(self):
        relatorio = SimpleNamespace(status="pendente_aprovacao", created_at=timezone.now())
        self.assertIsNone(motivo_link_comissao_encerrado(relatorio, "empresa"))

    def test_empresa_nao_ve_relatorio_ja_respondido(self):
        relatorio = SimpleNamespace(status="aprovado", created_at=timezone.now())
        self.assertIn("respondido", motivo_link_comissao_encerrado(relatorio, "empresa"))

    def test_link_vence_em_90_dias(self):
        relatorio = SimpleNamespace(
            status="pendente_aprovacao",
            created_at=timezone.now() - timedelta(days=91),
        )
        self.assertIn("venceu", motivo_link_comissao_encerrado(relatorio, "empresa"))


class SegredoDaLojaApiTests(_CrmApiTestBase):
    @patch("crm_vendas.views_crm_config_api.is_owner", return_value=False)
    @patch("crm_vendas.views_crm_config_api.get_current_loja_id")
    def test_vendedor_nao_grava_chave_asaas(self, mock_loja_id, _dono):
        mock_loja_id.return_value = self.loja.id
        response = self.client.patch(
            "/api/crm-vendas/config/",
            {"asaas_api_key": "$aact_prod_teste"},
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.content)

    @patch("crm_vendas.cache.CRMCacheManager.invalidate_dashboard")
    @patch("crm_vendas.serializers.CRMConfigSerializer")
    @patch("crm_vendas.views_crm_config_api._get_crm_config_for_loja")
    @patch("crm_vendas.views_crm_config_api.is_owner", return_value=False)
    @patch("crm_vendas.views_crm_config_api.get_current_loja_id")
    def test_vendedor_ainda_personaliza_o_pipeline(
        self, mock_loja_id, _dono, mock_cfg, mock_serializer, _cache,
    ):
        mock_loja_id.return_value = self.loja.id
        mock_cfg.return_value = MagicMock()
        serializer = mock_serializer.return_value
        serializer.is_valid.return_value = True
        serializer.data = {"origens_leads": ["Indicacao"]}
        response = self.client.patch(
            "/api/crm-vendas/config/",
            {"origens_leads": ["Indicacao"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        serializer.save.assert_called_once()
