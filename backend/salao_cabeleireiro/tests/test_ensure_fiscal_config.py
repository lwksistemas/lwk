"""Wiring e SQL idempotente das tabelas fiscais do salão."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from salao_cabeleireiro.schema_ensure import (
    MIGRATION_FISCAL,
    NFCE_CONFIG_TABLE,
    NFSE_CONFIG_TABLE,
    ensure_salao_fiscal_tables,
)


class _FakeCursor:
    def __init__(self, existing):
        self.existing = set(existing)
        self.executed = []
        self.db = SimpleNamespace(vendor="postgresql")
        self.connection = "postgresql"
        self._last_sql = ""
        self._last_params = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last_sql = sql
        self._last_params = params
        compact = " ".join(sql.split()).lower()
        if f"create table if not exists {NFSE_CONFIG_TABLE}" in compact:
            self.existing.add(NFSE_CONFIG_TABLE)
        if f"create table if not exists {NFCE_CONFIG_TABLE}" in compact:
            self.existing.add(NFCE_CONFIG_TABLE)

    def fetchone(self):
        sql = " ".join(self._last_sql.split()).lower()
        params = self._last_params or []
        if "information_schema.tables" in sql:
            name = params[0]
            return (1,) if name in self.existing else None
        return None


class TestSalaoFiscalSchemaWiring(SimpleTestCase):
    def test_ensure_registrado_no_deploy_e_auditoria(self):
        from superadmin.management.commands.ensure_all import ENSURES
        from superadmin.services.database_schema_service import _prefixos_tabela_app
        from superadmin.services.schema_audit_service import (
            ENSURE_COMANDOS_POR_TIPO,
            TABELAS_OBRIGATORIAS_POR_TIPO,
            TABELAS_PERMITIDAS_EXTRA_POR_TIPO,
            prefixos_tabela_para_app,
        )
        from superadmin.tenant_deploy import ENSURE_POR_APP

        names = [n for n, _ in ENSURES]
        self.assertIn("ensure_salao_fiscal_config", names)
        self.assertIn("ensure_salao_fiscal_config", ENSURE_POR_APP["salao_cabeleireiro"])
        self.assertIn(
            "ensure_salao_fiscal_config",
            ENSURE_COMANDOS_POR_TIPO["salao-cabeleireiro"],
        )
        self.assertIn(NFSE_CONFIG_TABLE, TABELAS_OBRIGATORIAS_POR_TIPO["salao-cabeleireiro"])
        self.assertIn(NFCE_CONFIG_TABLE, TABELAS_OBRIGATORIAS_POR_TIPO["salao-cabeleireiro"])
        self.assertIn(NFSE_CONFIG_TABLE, TABELAS_PERMITIDAS_EXTRA_POR_TIPO["salao-cabeleireiro"])
        self.assertIn(NFCE_CONFIG_TABLE, TABELAS_PERMITIDAS_EXTRA_POR_TIPO["salao-cabeleireiro"])
        self.assertEqual(
            _prefixos_tabela_app("salao_cabeleireiro"),
            ["salao_cabeleireiro_", "salao_nfse_config", "salao_nfce_config"],
        )
        self.assertEqual(
            prefixos_tabela_para_app("salao_cabeleireiro"),
            ["salao_cabeleireiro_", "salao_nfse_config", "salao_nfce_config"],
        )


class TestEnsureSalaoFiscalTables(SimpleTestCase):
    def test_cria_tabelas_quando_ausentes(self):
        cursor = _FakeCursor(set())
        self.assertTrue(ensure_salao_fiscal_tables(cursor))
        self.assertIn(NFSE_CONFIG_TABLE, cursor.existing)
        self.assertIn(NFCE_CONFIG_TABLE, cursor.existing)
        sqls = " ".join(sql for sql, _ in cursor.executed)
        self.assertIn(NFSE_CONFIG_TABLE, sqls)
        self.assertIn(NFCE_CONFIG_TABLE, sqls)
        self.assertIn("loja_id INTEGER NOT NULL", sqls)
        self.assertTrue(
            any(
                params == [MIGRATION_FISCAL, MIGRATION_FISCAL]
                for _, params in cursor.executed
            ),
        )

    def test_idempotente_quando_ja_existem(self):
        cursor = _FakeCursor({NFSE_CONFIG_TABLE, NFCE_CONFIG_TABLE})
        self.assertTrue(ensure_salao_fiscal_tables(cursor))
        creates = [
            sql for sql, _ in cursor.executed
            if "create table if not exists" in " ".join(sql.split()).lower()
        ]
        self.assertEqual(creates, [])

    def test_extras_do_salao_nao_listam_fiscais(self):
        from superadmin.services.schema_audit_service import listar_tabelas_extras_no_schema

        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("salao_cabeleireiro_cliente",),
            ("salao_nfse_config",),
            ("salao_nfce_config",),
            ("django_migrations",),
            ("legado_x",),
        ]
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor

        extras = listar_tabelas_extras_no_schema(
            conn,
            "loja_salao_teste",
            ["salao_cabeleireiro"],
            tipo_slug="salao-cabeleireiro",
        )
        self.assertEqual(extras, ["legado_x"])
