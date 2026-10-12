"""A busca do tomador não cruza o cadastro do outro app."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from nfse_integration import tomador_busca


class TomadorPorAppTest(SimpleTestCase):
    def test_clinica_nao_consulta_cliente_do_crm(self):
        with (
            patch.object(tomador_busca, "_loja_emite_nota_da_clinica", return_value=True),
            patch.object(tomador_busca, "_buscar_paciente_clinica", return_value=None) as paciente,
            patch.object(tomador_busca, "_buscar_conta_crm") as conta,
            patch.object(tomador_busca, "_buscar_lead_crm") as lead,
            patch.object(tomador_busca, "_buscar_nfse_por_documento", return_value=None),
        ):
            self.assertIsNone(tomador_busca.buscar_tomador_nfse_loja(6, "12345678901"))
        paciente.assert_called_once()
        conta.assert_not_called()
        lead.assert_not_called()

    def test_crm_nao_consulta_paciente(self):
        conta = SimpleNamespace(cnpj="12345678901", razao_social="Felix", nome="Felix", email="")
        with (
            patch.object(tomador_busca, "_loja_emite_nota_da_clinica", return_value=False),
            patch.object(tomador_busca, "_buscar_conta_crm", return_value=conta),
            patch.object(tomador_busca, "_payload_from_conta", return_value={"fonte": "conta"}) as payload,
            patch.object(tomador_busca, "_buscar_paciente_clinica") as paciente,
        ):
            self.assertEqual(
                tomador_busca.buscar_tomador_nfse_loja(4, "123.456.789-01"),
                {"fonte": "conta"},
            )
        payload.assert_called_once()
        paciente.assert_not_called()
