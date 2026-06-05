"""Serializers de estoque."""
from rest_framework import serializers

from ..models import ConsultaProdutoUtilizado, MovimentacaoEstoque, ProdutoEstoque


class ProdutoEstoqueSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    estoque_baixo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProdutoEstoque
        exclude = ['loja_id']


class ConsultaProdutoUtilizadoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    unidade_medida = serializers.CharField(source='produto.unidade_medida', read_only=True)
    quantidade_disponivel = serializers.DecimalField(
        source='produto.quantidade_atual', max_digits=10, decimal_places=2, read_only=True,
    )

    class Meta:
        model = ConsultaProdutoUtilizado
        exclude = ['loja_id']
        read_only_fields = ['estoque_baixado', 'created_at']


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(
        source='profissional.nome', read_only=True, default=None,
    )

    class Meta:
        model = MovimentacaoEstoque
        exclude = ['loja_id']
