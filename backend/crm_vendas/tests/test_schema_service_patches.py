"""Patches SQL do schema CRM — fora do hot path de requests."""
from unittest.mock import MagicMock, patch

from django.db.utils import ProgrammingError
from django.test import SimpleTestCase

from crm_vendas.schema_service import (
    apply_crm_tenant_schema_patches,
    patch_atividade_schema_on_column_error,
    patch_crm_vendas_atividade_columns_if_missing,
)


class PatchAtividadeSchemaOnColumnErrorTest(SimpleTestCase):
    def test_retorna_false_sem_db_name(self):
        exc = ProgrammingError('column lembrete_whatsapp does not exist')
        self.assertFalse(patch_atividade_schema_on_column_error(exc, None))

    def test_retorna_false_para_erro_nao_relacionado(self):
        exc = ProgrammingError('relation crm_vendas_foo does not exist')
        self.assertFalse(patch_atividade_schema_on_column_error(exc, 'loja_123'))

    @patch('crm_vendas.schema_service.patch_crm_vendas_atividade_columns_if_missing')
    def test_aplica_patch_para_coluna_atividade(self, mock_patch):
        exc = ProgrammingError('column "lembrete_whatsapp" does not exist')
        self.assertTrue(patch_atividade_schema_on_column_error(exc, 'loja_123'))
        mock_patch.assert_called_once_with('loja_123')


class ApplyCrmTenantSchemaPatchesTest(SimpleTestCase):
    @patch('crm_vendas.schema_service.patch_crm_vendas_atividade_columns_if_missing')
    @patch('crm_vendas.schema_service.patch_crm_vendas_asaas_columns_if_missing')
    def test_chama_ambos_patches(self, mock_asaas, mock_atividade):
        apply_crm_tenant_schema_patches('loja_99')
        mock_asaas.assert_called_once_with('loja_99')
        mock_atividade.assert_called_once_with('loja_99')


class PatchCrmVendasAtividadeColumnsTest(SimpleTestCase):
    @patch('core.db_config.ensure_loja_database_config', return_value=True)
    @patch('django.db.connections')
    def test_executa_alter_table_conta_e_lembrete(self, mock_connections, _mock_ensure):
        cursor = MagicMock()
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = cursor

        patch_crm_vendas_atividade_columns_if_missing('loja_1')

        sql_calls = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(any('conta_id' in sql for sql in sql_calls))
        self.assertTrue(any('lembrete_whatsapp' in sql for sql in sql_calls))
        self.assertTrue(any('django_migrations' in sql for sql in sql_calls))
