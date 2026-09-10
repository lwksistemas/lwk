"""Limpar legado não pode apagar django_migrations — senão o migrate recria as tabelas."""
import inspect

from django.test import SimpleTestCase

from superadmin.services.schema_audit_service import limpar_tabelas_extras_loja


class LimparExtrasHistoricoTest(SimpleTestCase):
    def test_nao_apaga_linhas_de_django_migrations(self):
        src = inspect.getsource(limpar_tabelas_extras_loja)
        self.assertNotIn("DELETE FROM django_migrations", src)
        self.assertIn("legacy_removed", src)
