"""migrate_all_lojas deve falhar o deploy quando alguma loja quebra."""
import inspect
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

_cifrar_mod = import_module("crm_vendas.migrations.0078_cifrar_senhas_issnet")
cifrar_senhas_issnet = _cifrar_mod.cifrar_senhas_issnet


class CifrarSenhasIssnetCrmMigrationTest(SimpleTestCase):
    def test_usa_banco_do_schema_editor(self):
        src = inspect.getsource(cifrar_senhas_issnet)
        self.assertIn("schema_editor.connection.alias", src)
        self.assertIn(".using(db)", src)
        self.assertIn("save(using=db", src)
        self.assertNotIn("del schema_editor", src)

    def test_consulta_no_alias_da_conexao(self):
        config = MagicMock()
        qs = MagicMock()
        qs.all.return_value = [config]
        model = MagicMock()
        model.objects.using.return_value = qs
        apps = MagicMock()
        apps.get_model.return_value = model
        schema_editor = MagicMock()
        schema_editor.connection.alias = "loja_crm_x"

        with patch(
            "core.encryption.cifrar_senhas_issnet_no_objeto",
            return_value=True,
        ) as cifrar:
            cifrar_senhas_issnet(apps, schema_editor)

        model.objects.using.assert_called_once_with("loja_crm_x")
        cifrar.assert_called_once_with(config)
        config.save.assert_called_once_with(
            using="loja_crm_x",
            update_fields=["issnet_senha", "issnet_senha_certificado"],
        )


class MigrateAllLojasExitCodeTest(SimpleTestCase):
    @patch.dict("os.environ", {"DATABASE_URL": "postgres://x"}, clear=False)
    @patch("superadmin.management.commands.migrate_all_lojas.call_command")
    @patch("superadmin.management.commands.migrate_all_lojas.settings")
    @patch("superadmin.management.commands.migrate_all_lojas.Loja")
    def test_falha_de_migrate_levanta_command_error(
        self, loja_model, settings_mock, call_cmd,
    ):
        settings_mock.DATABASES = {"loja_crm_x": {}}
        loja = SimpleNamespace(
            id=12,
            nome="CRM X",
            slug="crm-x",
            database_name="loja_crm_x",
            tipo_loja=SimpleNamespace(slug="crm-vendas"),
        )
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.__iter__ = lambda self: iter([loja])
        loja_model.objects.select_related.return_value.all.return_value = qs
        call_cmd.side_effect = RuntimeError("relation does not exist")

        with patch(
            "superadmin.management.commands.migrate_all_lojas.connections",
            {},
        ), patch(
            "core.db_config.ensure_loja_database_config",
            return_value=True,
        ), patch(
            "superadmin.services.migration_history_repair.repair_inconsistent_history",
            return_value=[],
        ), patch(
            "superadmin.tenant_deploy.filtrar_apps_loja",
            return_value=["crm_vendas"],
        ), patch(
            "tenants.middleware.set_current_tenant_db",
        ), patch(
            "tenants.middleware.set_current_loja_id",
        ):
            with self.assertRaises(CommandError) as ctx:
                call_command("migrate_all_lojas", apps=["crm_vendas"], verbosity=0)

        self.assertIn("migrate_all_lojas falhou", str(ctx.exception))
        self.assertIn("crm-x/crm_vendas", str(ctx.exception))
