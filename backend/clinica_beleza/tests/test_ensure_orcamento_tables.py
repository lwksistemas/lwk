"""Wiring e SQL idempotente das tabelas de orçamento da consulta."""
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.schema_ensure import (
    CONSULTA_TABLE,
    MIGRATION_ORCAMENTO,
    MIGRATION_ORCAMENTO_ITEM_LOJA,
    ORCAMENTO_CONSULTA_TABLE,
    ORCAMENTO_ITEM_TABLE,
    PATIENT_TABLE,
    PROCEDURE_TABLE,
    PROFESSIONAL_TABLE,
    ensure_orcamento_tables,
)

Migration = import_module("clinica_beleza.migrations.0077_orcamento_consulta").Migration


class _FakeCursor:
    def __init__(self, existing, id_types=None):
        self.existing = set(existing)
        self.id_types = dict(id_types or {})
        self.columns = {}
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
        if f"create table {ORCAMENTO_CONSULTA_TABLE}" in compact:
            self.existing.add(ORCAMENTO_CONSULTA_TABLE)
        if f"create table {ORCAMENTO_ITEM_TABLE}" in compact:
            self.existing.add(ORCAMENTO_ITEM_TABLE)
            self.columns[ORCAMENTO_ITEM_TABLE] = {"id", "loja_id", "orcamento_id"}
        if "add column loja_id" in compact:
            self.columns.setdefault(ORCAMENTO_ITEM_TABLE, set()).add("loja_id")

    def fetchone(self):
        sql = " ".join(self._last_sql.split()).lower()
        params = self._last_params or []
        if "information_schema.tables" in sql:
            name = params[0]
            return (1,) if name in self.existing else None
        if "information_schema.columns" in sql:
            if len(params) >= 2:
                table, col = params[0], params[1]
                return (1,) if col in self.columns.get(table, set()) else None
            table = params[0]
            return (self.id_types.get(table, "bigint"),)
        return None


class TestOrcamentoSchemaWiring(SimpleTestCase):
    def test_migration_0077_cria_os_dois_models(self):
        names = [
            op.name for op in Migration.operations if op.__class__.__name__ == "CreateModel"
        ]
        self.assertEqual(names, ["OrcamentoConsulta", "OrcamentoItem"])
        self.assertEqual(Migration.dependencies, [("clinica_beleza", "0076_pedido_compra_paciente")])
        m0078 = import_module("clinica_beleza.migrations.0078_orcamento_item_loja_id").Migration
        self.assertEqual(m0078.dependencies, [("clinica_beleza", "0077_orcamento_consulta")])

    def test_ensure_registrado_no_deploy_e_auditoria(self):
        from superadmin.management.commands.ensure_all import ENSURES
        from superadmin.services.schema_audit_service import (
            ENSURE_COMANDOS_POR_TIPO,
            TABELAS_OBRIGATORIAS_POR_TIPO,
        )
        from superadmin.tenant_deploy import ENSURE_POR_APP

        names = [n for n, _ in ENSURES]
        self.assertIn("ensure_orcamento_tables", names)
        self.assertIn("ensure_orcamento_tables", ENSURE_POR_APP["clinica_beleza"])
        self.assertIn("ensure_orcamento_tables", ENSURE_COMANDOS_POR_TIPO["clinica-beleza"])
        self.assertIn(
            ORCAMENTO_CONSULTA_TABLE,
            TABELAS_OBRIGATORIAS_POR_TIPO["clinica-beleza"],
        )
        self.assertIn(
            ORCAMENTO_ITEM_TABLE,
            TABELAS_OBRIGATORIAS_POR_TIPO["clinica-beleza"],
        )


class TestEnsureOrcamentoTables(SimpleTestCase):
    def test_cria_tabelas_quando_ausentes(self):
        cursor = _FakeCursor(
            {CONSULTA_TABLE, PATIENT_TABLE, PROFESSIONAL_TABLE, PROCEDURE_TABLE},
        )
        self.assertTrue(ensure_orcamento_tables(cursor))
        self.assertIn(ORCAMENTO_CONSULTA_TABLE, cursor.existing)
        self.assertIn(ORCAMENTO_ITEM_TABLE, cursor.existing)
        sqls = " ".join(sql for sql, _ in cursor.executed)
        self.assertIn(ORCAMENTO_CONSULTA_TABLE, sqls)
        self.assertIn(ORCAMENTO_ITEM_TABLE, sqls)
        self.assertIn("loja_id INTEGER NOT NULL", sqls)
        self.assertTrue(
            any(
                params == [MIGRATION_ORCAMENTO, MIGRATION_ORCAMENTO]
                for _, params in cursor.executed
            ),
        )

    def test_idempotente_quando_ja_existem(self):
        cursor = _FakeCursor({
            CONSULTA_TABLE,
            PATIENT_TABLE,
            PROFESSIONAL_TABLE,
            PROCEDURE_TABLE,
            ORCAMENTO_CONSULTA_TABLE,
            ORCAMENTO_ITEM_TABLE,
        })
        self.assertTrue(ensure_orcamento_tables(cursor))
        sqls = " ".join(sql for sql, _ in cursor.executed)
        self.assertNotIn("CREATE TABLE", sqls)
        self.assertIn("ADD COLUMN loja_id", sqls)
        self.assertTrue(
            any(
                params == [MIGRATION_ORCAMENTO_ITEM_LOJA, MIGRATION_ORCAMENTO_ITEM_LOJA]
                for _, params in cursor.executed
            ),
        )

    def test_nao_recria_quando_item_ja_tem_loja_id(self):
        cursor = _FakeCursor({
            CONSULTA_TABLE,
            PATIENT_TABLE,
            PROFESSIONAL_TABLE,
            PROCEDURE_TABLE,
            ORCAMENTO_CONSULTA_TABLE,
            ORCAMENTO_ITEM_TABLE,
        })
        cursor.columns[ORCAMENTO_ITEM_TABLE] = {"id", "loja_id", "orcamento_id"}
        self.assertTrue(ensure_orcamento_tables(cursor))
        sqls = " ".join(sql for sql, _ in cursor.executed)
        self.assertNotIn("ADD COLUMN loja_id", sqls)
        self.assertIn("SET loja_id = o.loja_id", sqls)

    def test_nao_cria_sem_tabela_de_consulta(self):
        cursor = _FakeCursor({PATIENT_TABLE, PROFESSIONAL_TABLE, PROCEDURE_TABLE})
        with patch("clinica_beleza.schema_ensure.logger"):
            self.assertFalse(ensure_orcamento_tables(cursor))
        sqls = " ".join(sql for sql, _ in cursor.executed)
        self.assertNotIn("CREATE TABLE", sqls)

    def test_fk_acompanha_integer_de_loja_antiga(self):
        cursor = _FakeCursor(
            {CONSULTA_TABLE, PATIENT_TABLE, PROFESSIONAL_TABLE, PROCEDURE_TABLE},
            id_types={
                CONSULTA_TABLE: "integer",
                PATIENT_TABLE: "integer",
                PROFESSIONAL_TABLE: "integer",
                PROCEDURE_TABLE: "integer",
            },
        )
        self.assertTrue(ensure_orcamento_tables(cursor))
        create_sql = next(
            sql for sql, _ in cursor.executed if f"CREATE TABLE {ORCAMENTO_CONSULTA_TABLE}" in sql
        )
        self.assertIn("consulta_id INTEGER NOT NULL", create_sql)
        self.assertNotIn("consulta_id BIGINT", create_sql)
