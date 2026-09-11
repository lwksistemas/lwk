"""Serializers de fornecedor e catálogo."""
from rest_framework import serializers

from ..models.fornecedores import Fornecedor, FornecedorProduto


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        exclude = ["loja_id"]


class FornecedorProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FornecedorProduto
        exclude = ["loja_id"]
        read_only_fields = ["fornecedor", "created_at", "updated_at"]
