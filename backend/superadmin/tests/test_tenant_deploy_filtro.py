"""Filtro de migrate/ensure pontual por app."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from superadmin.tenant_deploy import (
    ENSURE_POR_APP,
    ensures_para_apps,
    filtrar_apps_loja,
    parse_apps_option,
)


class TenantDeployFiltroTest(SimpleTestCase):
    def test_parse_apps_virgula_e_lista(self):
        self.assertEqual(
            parse_apps_option(["clinica_beleza,whatsapp", "nfse_integration"]),
            ["clinica_beleza", "whatsapp", "nfse_integration"],
        )

    def test_clinica_nao_cria_tabela_em_loja_crm(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-vendas"))
        self.assertEqual(filtrar_apps_loja(loja, ["clinica_beleza"]), [])

    def test_crm_em_clinica_ainda_pode_migrar_crm(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza"))
        self.assertEqual(filtrar_apps_loja(loja, ["crm_vendas"]), ["crm_vendas"])

    def test_clinica_migra_so_clinica_beleza(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza"))
        self.assertEqual(filtrar_apps_loja(loja, ["clinica_beleza"]), ["clinica_beleza"])

    def test_ensure_clinica_nao_inclui_crm(self):
        all_ensures = [
            ("ensure_clinica_beleza_consultas", {}),
            ("ensure_crm_config_colunas", {}),
            ("ensure_whatsapp_evolution_fields", {}),
            ("setup_security_schedules", {}),
        ]
        out = ensures_para_apps(["clinica_beleza"], all_ensures)
        names = [n for n, _ in out]
        self.assertEqual(names, ["ensure_clinica_beleza_consultas"])
        self.assertTrue("ensure_crm_config_colunas" in ENSURE_POR_APP["crm_vendas"])
