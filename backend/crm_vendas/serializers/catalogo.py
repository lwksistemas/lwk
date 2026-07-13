"""Serializers de catálogo produtos/serviços."""
from rest_framework import serializers

from core.serializer_mixins import (
    TextNormalizationMixin,
)

from ..models import CategoriaProdutoServico, ProdutoServico


class CategoriaProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()
    uppercase_fields = ["nome"]

    class Meta:
        model = CategoriaProdutoServico
        fields = [
            "id", "nome", "descricao", "cor", "ordem", "ativo",
            "produtos_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_produtos_count(self, obj):
        """Retorna quantidade de produtos/serviços nesta categoria"""
        return obj.produtos_servicos.filter(ativo=True).count()


class ProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)
    categoria_cor = serializers.CharField(source="categoria.cor", read_only=True)
    uppercase_fields = ["nome", "codigo"]

    class Meta:
        model = ProdutoServico
        fields = [
            "id", "tipo", "codigo", "nome", "descricao", "categoria",
            "categoria_nome", "categoria_cor", "preco", "recorrencia", "ativo",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
