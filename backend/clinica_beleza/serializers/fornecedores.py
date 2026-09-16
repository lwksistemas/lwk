"""Serializers de fornecedor e catálogo."""
from rest_framework import serializers

from ..models.fornecedores import Fornecedor, FornecedorProduto


class FornecedorSerializer(serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()

    class Meta:
        model = Fornecedor
        exclude = ["loja_id"]

    def get_produtos_count(self, obj):
        count = getattr(obj, "produtos_count", None)
        if count is not None:
            return int(count)
        return obj.produtos.count()


class FornecedorProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FornecedorProduto
        exclude = ["loja_id"]
        read_only_fields = ["fornecedor", "created_at", "updated_at"]
