"""Schema loja_* só aceita apps do tipo da loja — não recria legado."""
from django.test import SimpleTestCase

from config.db_router import MultiTenantRouter, _apps_permitidos_schema_loja


class TenantAllowMigrateTest(SimpleTestCase):
    def setUp(self):
        self.r = MultiTenantRouter()

    def test_apps_do_crm_podem_migrar_no_tenant(self):
        for app in ("crm_vendas", "whatsapp", "nfse_integration", "stores", "auth"):
            self.assertTrue(self.r.allow_migrate("loja_felix", app), app)

    def test_clinica_geral_pode_migrar_no_tenant(self):
        self.assertTrue(self.r.allow_migrate("loja_clinica", "clinica_geral"))

    def test_asaas_admin_e_blacklist_nao_migram_no_tenant(self):
        for app in ("asaas_integration", "admin", "sessions", "token_blacklist"):
            self.assertFalse(self.r.allow_migrate("loja_felix", app), app)

    def test_asaas_continua_no_default(self):
        self.assertTrue(self.r.allow_migrate("default", "asaas_integration"))

    def test_allowlist_inclui_todos_os_tipos(self):
        permitidos = _apps_permitidos_schema_loja()
        self.assertIn("clinica_beleza", permitidos)
        self.assertIn("clinica_geral", permitidos)
        self.assertNotIn("asaas_integration", permitidos)
