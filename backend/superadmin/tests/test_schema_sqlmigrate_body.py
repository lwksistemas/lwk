"""SQL do sqlmigrate no tenant não pode trazer BEGIN/COMMIT da transação do Django."""
from django.test import SimpleTestCase

from superadmin.services.database_schema_service import _sqlmigrate_body


class SqlmigrateBodyTest(SimpleTestCase):
    def test_remove_begin_commit(self):
        sql = "BEGIN;\nCREATE TABLE nfse_integration_nfse (id integer);\nCOMMIT;"
        self.assertEqual(
            _sqlmigrate_body(sql),
            "CREATE TABLE nfse_integration_nfse (id integer);",
        )

    def test_vazio_vira_vazio(self):
        self.assertEqual(_sqlmigrate_body(""), "")
        self.assertEqual(_sqlmigrate_body("BEGIN;\nCOMMIT;"), "")
