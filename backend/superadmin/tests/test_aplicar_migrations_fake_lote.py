"""Testes do atalho --fake em lote quando há tabelas sem histórico de migration."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from superadmin.services.database_schema_service import (
    _contar_tabelas_app_no_schema,
    _prefixos_tabela_app,
)
from superadmin.services.schema_audit_service import prefixos_tabela_para_app


class PrefixosCrmVendasTest(SimpleTestCase):
    def test_crm_vendas_inclui_financeiro_no_schema_service(self):
        self.assertEqual(
            _prefixos_tabela_app("crm_vendas"),
            ["crm_vendas_", "crm_financeiro_"],
        )

    def test_crm_vendas_inclui_financeiro_na_auditoria(self):
        self.assertEqual(
            prefixos_tabela_para_app("crm_vendas"),
            ["crm_vendas_", "crm_financeiro_"],
        )


class ContarTabelasAppTest(SimpleTestCase):
    def test_conta_com_multiplos_prefixos(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (16,)
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor

        n = _contar_tabelas_app_no_schema(conn, "loja_x", "crm_vendas")
        self.assertEqual(n, 16)
        sql = cursor.execute.call_args[0][0]
        self.assertIn("LIKE %s", sql)
        params = cursor.execute.call_args[0][1]
        self.assertEqual(params[0], "loja_x")
        self.assertIn("crm_vendas_%", params)
        self.assertIn("crm_financeiro_%", params)
