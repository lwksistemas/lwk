"""Backup da clínica não inclui tabelas de CRM nem log de WhatsApp."""
from types import SimpleNamespace
from django.test import SimpleTestCase

from superadmin.backup_service.service import _filtrar_tabelas_por_tipo_loja


class FiltroBackupTipoLojaTest(SimpleTestCase):
    def test_clinica_nao_exporta_crm_nem_log_whatsapp(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza"))
        tabelas = [
            "clinica_beleza_patient",
            "clinica_beleza_appointment",
            "whatsapp_whatsappconfig",
            "whatsapp_whatsapplog",
            "crm_vendas_contato",
            "crm_vendas_proposta",
            "stores_store",
            "products_product",
        ]
        out = _filtrar_tabelas_por_tipo_loja(loja, tabelas)
        self.assertEqual(
            out,
            [
                "clinica_beleza_patient",
                "clinica_beleza_appointment",
                "whatsapp_whatsappconfig",
            ],
        )

    def test_crm_continua_exportando_tabelas_do_crm(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-vendas"))
        tabelas = ["crm_vendas_contato", "clinica_beleza_patient", "whatsapp_whatsapplog"]
        out = _filtrar_tabelas_por_tipo_loja(loja, tabelas)
        self.assertEqual(out, ["crm_vendas_contato"])
