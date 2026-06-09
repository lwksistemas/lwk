from rest_framework import serializers
from core.serializer_mixins import TextNormalizationMixin
from .models import Categoria, Produto, Cliente, Pedido, ItemPedido, Cupom


class CategoriaSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome']
    phone_fields = []

    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ProdutoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    uppercase_fields = ['nome']
    phone_fields = []

    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ClienteSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome', 'cidade', 'estado', 'bairro']
    phone_fields = ['telefone']

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = ItemPedido
        fields = '__all__'
        read_only_fields = ['created_at']


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CupomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cupom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
