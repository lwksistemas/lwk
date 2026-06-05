"""Serializers de estoque."""
from rest_framework import serializers

from ..models import MovimentacaoEstoque, ProdutoEstoque


class ProdutoEstoqueSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    estoque_baixo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProdutoEstoque
        exclude = ['loja_id']


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(
        source='profissional.nome', read_only=True, default=None,
    )

    class Meta:
        model = MovimentacaoEstoque
        exclude = ['loja_id']
