from rest_framework import serializers
from .models import Categoria, ItemCardapio, Mesa, Cliente, Reserva, Pedido, ItemPedido, Funcionario


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ItemCardapioSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)

    class Meta:
        model = ItemCardapio
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ReservaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)

    class Meta:
        model = Reserva
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ItemPedidoSerializer(serializers.ModelSerializer):
    item_nome = serializers.CharField(source='item_cardapio.nome', read_only=True)

    class Meta:
        model = ItemPedido
        fields = '__all__'
        read_only_fields = ['created_at']


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
