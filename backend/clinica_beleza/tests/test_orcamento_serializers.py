"""Serializers POST/PATCH de orçamento."""
from django.test import SimpleTestCase

from clinica_beleza.serializers import OrcamentoCreateSerializer, OrcamentoStatusSerializer


class OrcamentoCreateSerializerTest(SimpleTestCase):
    def test_exige_ao_menos_um_item(self):
        serializer = OrcamentoCreateSerializer(data={"consulta_id": 1, "itens": []})
        self.assertFalse(serializer.is_valid())
        self.assertIn("itens", serializer.errors)

    def test_exige_consulta_e_procedimento(self):
        serializer = OrcamentoCreateSerializer(data={"itens": [{"quantidade": 1}]})
        self.assertFalse(serializer.is_valid())
        self.assertIn("consulta_id", serializer.errors)
        self.assertIn("itens", serializer.errors)

    def test_payload_valido(self):
        serializer = OrcamentoCreateSerializer(
            data={
                "consulta_id": 10,
                "observacoes": "Pix",
                "validade_dias": 15,
                "itens": [
                    {"procedure_id": 3, "valor_customizado": "120.50", "quantidade": 2},
                ],
            },
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["consulta_id"], 10)
        self.assertEqual(len(serializer.validated_data["itens"]), 1)


class OrcamentoStatusSerializerTest(SimpleTestCase):
    def test_aceita_aceito_e_recusado(self):
        for status in ("ACEITO", "RECUSADO"):
            serializer = OrcamentoStatusSerializer(data={"status": status})
            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejeita_enviado_e_rascunho(self):
        for status in ("ENVIADO", "RASCUNHO", "pago"):
            serializer = OrcamentoStatusSerializer(data={"status": status})
            self.assertFalse(serializer.is_valid())
