"""O sync do .env não cobre uma chave Asaas já válida no banco."""
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

CHAVE_BANCO = "$aact_prod_" + ("a" * 40)
CHAVE_ENV = "$aact_prod_" + ("b" * 40)


@override_settings(ASAAS_API_KEY=CHAVE_ENV, ASAAS_INTEGRATION_ENABLED=True)
class SyncAsaasConfigFromEnvTest(SimpleTestCase):
    def _rodar(self, db_key):
        config = MagicMock()
        config.api_key_decrypted = db_key
        out, err = StringIO(), StringIO()
        with patch(
            "asaas_integration.management.commands.sync_asaas_config_from_env.AsaasConfig.get_config",
            return_value=config,
        ):
            call_command("sync_asaas_config_from_env", stdout=out, stderr=err)
        return config, out.getvalue(), err.getvalue()

    def test_nao_sobrescreve_chave_valida_diferente(self):
        config, _out, err = self._rodar(CHAVE_BANCO)
        config.save.assert_not_called()
        self.assertIn("Nada foi alterado", err)

    def test_copia_quando_o_banco_esta_invalido(self):
        config, out, err = self._rodar("chave-velha")
        self.assertEqual(config.api_key, CHAVE_ENV)
        config.save.assert_called_once()
        self.assertIn("Chave sincronizada", out)
        self.assertEqual(err, "")
