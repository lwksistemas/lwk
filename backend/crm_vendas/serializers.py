from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import Lead, Cliente, Vendedor, Produto, Venda, Pipeline


class LeadSerializer(BaseLojaSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ClienteSerializer(BaseLojaSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class VendedorSerializer(BaseLojaSerializer):
    class Meta:
        model = Vendedor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class VendaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
