"""CPF e CNPJ não reaproveitam o mesmo cliente Asaas pelo e-mail."""
from unittest.mock import patch

from django.test import SimpleTestCase

from asaas_integration.client import AsaasClient


class ClienteCpfCnpjTest(SimpleTestCase):
    def _client(self) -> AsaasClient:
        return AsaasClient(api_key="$aact_hmlg_teste", sandbox=True)

    def test_cnpj_nao_usa_cliente_do_cpf_pelo_email(self):
        cliente = self._client()
        cpf = {"id": "cus_cpf", "cpfCnpj": "12345678901", "email": "loja@exemplo.com"}

        def buscar(_method, endpoint, params=None):
            self.assertEqual(endpoint, "customers")
            self.assertNotIn("email", params or {})
            if params.get("cpfCnpj") == "12345678000199":
                return {"data": []}
            return {"data": [cpf]}

        with patch.object(cliente, "_make_request", side_effect=buscar):
            achado = cliente.search_customer(
                cpf_cnpj="12.345.678/0001-99",
                email="loja@exemplo.com",
                external_reference="loja_felix",
            )
        self.assertIsNone(achado)

    def test_cpf_encontra_so_o_mesmo_documento(self):
        cliente = self._client()
        with patch.object(
            cliente,
            "_make_request",
            return_value={"data": [{"id": "cus_cpf", "cpfCnpj": "123.456.789-01"}]},
        ):
            achado = cliente.search_customer(cpf_cnpj="12345678901", email="outro@exemplo.com")
        self.assertEqual(achado["id"], "cus_cpf")
