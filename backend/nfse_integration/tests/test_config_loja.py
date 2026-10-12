"""O motor de NFS-e usa o registro do app, sem importar o outro."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from nfse_integration import config_loja


class ConfigLojaNfseTest(SimpleTestCase):
    def test_tipo_registrado_nao_cai_no_padrao(self):
        loja = SimpleNamespace(id=9, tipo_loja=SimpleNamespace(codigo="ZZTEST"))
        marker = object()

        def getter(recebida):
            self.assertIs(recebida, loja)
            return marker

        anterior = config_loja._por_tipo.get("ZZTEST")
        config_loja.registrar_config_nfse_tipos(frozenset({"ZZTEST"}), getter)
        try:
            self.assertIs(config_loja.config_nfse_da_loja(loja), marker)
        finally:
            if anterior is None:
                config_loja._por_tipo.pop("ZZTEST", None)
            else:
                config_loja._por_tipo["ZZTEST"] = anterior

    def test_clinica_e_crm_registram_getters_diferentes(self):
        self.assertIn("CLIBEL", config_loja._por_tipo)
        self.assertIn("CLIEST", config_loja._por_tipo)
        self.assertIsNotNone(config_loja._padrao)
        self.assertIsNot(config_loja._por_tipo["CLIBEL"], config_loja._padrao)
