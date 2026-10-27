"""Lead com empresa grava a pessoa como contato dessa empresa."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.serializers.leads import LeadSerializer


class LeadCriaContatoTests(SimpleTestCase):
    def test_cria_contato_novo_na_empresa(self):
        conta = MagicMock(id=4)
        contato = MagicMock()
        serializer = LeadSerializer()
        with patch("crm_vendas.serializers.leads.Contato") as modelo:
            modelo.objects.filter.return_value.first.return_value = None
            modelo.objects.create.return_value = contato
            achado = serializer._contato_da_empresa(
                conta,
                {"nome": "Ana", "email": "ana@felix.com", "telefone": "11999999999"},
                "Compras",
            )
        modelo.objects.create.assert_called_once_with(
            conta=conta,
            nome="Ana",
            email="ana@felix.com",
            telefone="11999999999",
            cargo="Compras",
        )
        self.assertIs(achado, contato)

    def test_reaproveita_contato_do_mesmo_nome(self):
        conta = MagicMock(id=4)
        existente = MagicMock()
        serializer = LeadSerializer()
        with patch("crm_vendas.serializers.leads.Contato") as modelo:
            modelo.objects.filter.return_value.first.return_value = existente
            achado = serializer._contato_da_empresa(
                conta,
                {"nome": "Ana", "email": "ana@felix.com", "telefone": ""},
                "",
            )
        modelo.objects.create.assert_not_called()
        existente.save.assert_called_once()
        self.assertIs(achado, existente)

    def test_create_liga_o_contato_quando_ha_empresa(self):
        conta = MagicMock(id=4)
        contato = MagicMock()
        serializer = LeadSerializer()
        salvo = {}

        def gravar(_self, validated_data):
            salvo.update(validated_data)
            return validated_data

        with patch.object(serializer, "_contato_da_empresa", return_value=contato), patch(
            "rest_framework.serializers.ModelSerializer.create",
            gravar,
        ):
            serializer.create({"nome": "ANA", "conta": conta, "cargo": "DIRETOR"})
        self.assertIs(salvo["contato"], contato)
        self.assertNotIn("cargo", salvo)
