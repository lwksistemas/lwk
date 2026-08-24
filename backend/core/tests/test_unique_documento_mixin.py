"""UniqueDocumentoPerLojaMixin — erro de duplicata no campo, não em non_field_errors."""
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework import serializers

from core.serializer_mixins import UniqueDocumentoPerLojaMixin


class _DummyLead:
    pass


class _LeadDocSerializer(UniqueDocumentoPerLojaMixin, serializers.Serializer):
    unique_documento_fields = ["cpf_cnpj"]
    unique_documento_entidade = "lead"
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = _DummyLead


class TestUniqueDocumentoMixin(SimpleTestCase):
    @patch("core.serializer_mixins.existe_documento_duplicado", return_value=True)
    @patch("tenants.middleware.get_current_loja_id", return_value=4)
    def test_duplicado_retorna_erro_no_campo(self, _loja, _dup):
        ser = _LeadDocSerializer(data={"cpf_cnpj": "529.982.247-25"})
        self.assertFalse(ser.is_valid())
        self.assertIn("cpf_cnpj", ser.errors)
        self.assertNotIn("non_field_errors", ser.errors)
        self.assertIn("Já existe um lead", str(ser.errors["cpf_cnpj"][0]))

    @patch("core.serializer_mixins.existe_documento_duplicado", return_value=False)
    @patch("tenants.middleware.get_current_loja_id", return_value=4)
    def test_documento_livre_valida(self, _loja, _dup):
        ser = _LeadDocSerializer(data={"cpf_cnpj": "529.982.247-25"})
        self.assertTrue(ser.is_valid(), ser.errors)
