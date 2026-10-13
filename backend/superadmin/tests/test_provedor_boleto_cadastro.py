"""Cadastro público usa o provedor marcado em Recebimento das assinaturas."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from superadmin.provedor_boleto import provedor_boleto_padrao, provedor_no_cadastro


def _config(*, use_for_boletos=False, enabled=False):
    return SimpleNamespace(use_for_boletos=use_for_boletos, enabled=enabled)


class ProvedorBoletoCadastroTests(SimpleTestCase):
    def test_sem_marca_fica_asaas(self):
        with (
            patch("superadmin.models.CoraConfig.get_config", return_value=_config()),
            patch("superadmin.models.MercadoPagoConfig.get_config", return_value=_config()),
        ):
            self.assertEqual(provedor_boleto_padrao(), "asaas")

    def test_cora_marcada_e_ligada(self):
        with (
            patch(
                "superadmin.models.CoraConfig.get_config",
                return_value=_config(use_for_boletos=True, enabled=True),
            ),
            patch("superadmin.models.MercadoPagoConfig.get_config", return_value=_config()),
        ):
            self.assertEqual(provedor_boleto_padrao(), "cora")

    def test_cora_marcada_mas_desligada_nao_entra(self):
        with (
            patch(
                "superadmin.models.CoraConfig.get_config",
                return_value=_config(use_for_boletos=True, enabled=False),
            ),
            patch(
                "superadmin.models.MercadoPagoConfig.get_config",
                return_value=_config(use_for_boletos=True, enabled=True),
            ),
        ):
            self.assertEqual(provedor_boleto_padrao(), "mercadopago")

    def test_cadastro_publico_ignora_asaas_enviado(self):
        anonimo = SimpleNamespace(is_superuser=False)
        with patch("superadmin.provedor_boleto.provedor_boleto_padrao", return_value="cora"):
            self.assertEqual(provedor_no_cadastro(anonimo, "asaas"), "cora")

    def test_superadmin_mantem_a_escolha(self):
        admin = SimpleNamespace(is_superuser=True)
        with patch("superadmin.provedor_boleto.provedor_boleto_padrao", return_value="cora"):
            self.assertEqual(provedor_no_cadastro(admin, "asaas"), "asaas")
