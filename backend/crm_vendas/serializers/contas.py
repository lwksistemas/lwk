"""Serializers de contas CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Conta


class ContaSerializer(
    CpfCnpjNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    cpf_cnpj_fields = ["cnpj"]
    unique_documento_fields = ["cnpj"]
    unique_documento_entidade = "empresa"
    phone_fields = ["telefone"]
    uppercase_fields = ["nome", "razao_social", "segmento", "cidade", "bairro", "uf"]

    class Meta:
        model = Conta
        fields = [
            "id", "nome", "razao_social", "cnpj", "inscricao_estadual", "tipo", "segmento",
            "telefone", "email", "site",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "endereco", "observacoes", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

