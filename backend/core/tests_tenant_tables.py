"""Testes de helpers de schema tenant."""
from django.test import SimpleTestCase

from core.tenant_tables import tenant_table_exists


class TenantTableExistsTest(SimpleTestCase):
    def test_default_db_retorna_false(self):
        self.assertFalse(tenant_table_exists("default", "whatsapp_whatsappconfig"))
