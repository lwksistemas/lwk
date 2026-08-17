"""CONN_MAX_AGE do tenant não herda o pool do public."""
import os
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.db_config import (
    _default_tenant_conn_max_age,
    close_tenant_connections,
    ensure_loja_database_config,
)


class TenantConnMaxAgeTest(SimpleTestCase):
    def test_padrao_e_zero(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TENANT_CONN_MAX_AGE", None)
            os.environ["CONN_MAX_AGE"] = "120"
            self.assertEqual(_default_tenant_conn_max_age(), 0)

    def test_override_por_env(self):
        with patch.dict(os.environ, {"TENANT_CONN_MAX_AGE": "30"}):
            self.assertEqual(_default_tenant_conn_max_age(), 30)

    @override_settings(DATABASES={"default": {}, "loja_x": {"CONN_MAX_AGE": 120}})
    def test_nao_promove_pool_no_tenant(self):
        with patch.dict(os.environ, {"TENANT_CONN_MAX_AGE": "0"}):
            self.assertTrue(ensure_loja_database_config("loja_x"))
            from django.conf import settings
            self.assertEqual(settings.DATABASES["loja_x"]["CONN_MAX_AGE"], 0)

    @override_settings(DATABASES={"default": {}, "suporte": {}, "loja_x": {}})
    def test_fecha_so_alias_de_loja(self):
        closed = []

        class FakeConn:
            def close(self):
                closed.append(self.alias)

        class FakeConnections:
            databases = {"default": {}, "suporte": {}, "loja_x": {}}

            def __getitem__(self, alias):
                conn = FakeConn()
                conn.alias = alias
                return conn

        with patch("django.db.connections", FakeConnections()):
            close_tenant_connections()
        self.assertEqual(closed, ["loja_x"])

    def test_hook_django_q_fecha_tenant(self):
        from core.q_signals import close_tenant_after_task

        with patch("core.db_config.close_tenant_connections") as mock_close:
            close_tenant_after_task({"id": 1})
            mock_close.assert_called_once()
