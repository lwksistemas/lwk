"""Limpar legado não pode apagar django_migrations — senão o migrate recria as tabelas."""
import inspect

from django.test import SimpleTestCase

from clinica_beleza.schema_ensure import queryset_lojas_clinica_beleza
from superadmin.services.database_schema_service import apps_permitidos_para_tipo, tipo_usa_app
from superadmin.services.schema_audit_service import limpar_tabelas_extras_loja


class LimparExtrasHistoricoTest(SimpleTestCase):
    def test_nao_apaga_linhas_de_django_migrations(self):
        src = inspect.getsource(limpar_tabelas_extras_loja)
        self.assertNotIn("DELETE FROM django_migrations", src)
        self.assertIn("legacy_removed", src)

    def test_crm_nao_recebe_tabela_de_clinica(self):
        self.assertFalse(tipo_usa_app("crm-vendas", "clinica_beleza"))
        self.assertTrue(tipo_usa_app("clinica-beleza", "clinica_beleza"))
        self.assertNotIn("clinica_beleza", apps_permitidos_para_tipo("crm-vendas"))

    def test_ensure_so_lista_loja_clinica(self):
        src = inspect.getsource(queryset_lojas_clinica_beleza)
        self.assertIn("tipo_loja__slug__in", src)
        self.assertIn("clinica_beleza", src)
