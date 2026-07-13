"""Garante que emissão NFS-e na fila configura o schema da loja."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from nfse_integration.queue_tasks import run_emissao_nfse_loja


class NFSeQueueTenantTest(TestCase):
    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja_sync")
    @patch("tenants.middleware._configure_tenant_db_for_loja", return_value=True)
    @patch("superadmin.models.Loja")
    def test_run_emissao_configura_tenant_antes_de_emitir(
        self, mock_loja_cls, mock_configure_tenant, mock_processar,
    ):
        loja = MagicMock(id=7, database_name="loja_felix")
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja
        mock_processar.return_value = ({"success": True}, 201)

        run_emissao_nfse_loja(7, {"servico_descricao": "Teste", "valor_servicos": "10"})

        mock_configure_tenant.assert_called_once_with(loja)
        mock_processar.assert_called_once()

    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja_sync")
    @patch("tenants.middleware._configure_tenant_db_for_loja", return_value=False)
    @patch("superadmin.models.Loja")
    def test_run_emissao_aborta_sem_tenant(self, mock_loja_cls, _configure, mock_processar):
        loja = MagicMock(id=7)
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja

        run_emissao_nfse_loja(7, {"servico_descricao": "Teste", "valor_servicos": "10"})

        mock_processar.assert_not_called()
