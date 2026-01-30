from rest_framework import serializers
from .models import (
    Categoria, ItemCardapio, Mesa, Cliente, Reserva, Pedido, ItemPedido, Funcionario,
    Fornecedor, NotaFiscalEntrada, ItemNotaFiscalEntrada, EstoqueItem, MovimentoEstoque,
    RegistroPesoBalança
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'descricao', 'ordem', 'is_active', 'created_at', 'updated_at', 'loja_id']
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class ItemCardapioSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)

    class Meta:
        model = ItemCardapio
        fields = [
            'id', 'nome', 'descricao', 'categoria', 'categoria_nome', 'preco', 'tempo_preparo',
            'imagem_url', 'ingredientes', 'calorias', 'is_disponivel', 'is_destaque',
            'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'categoria_nome', 'created_at', 'updated_at', 'loja_id']


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = [
            'id', 'numero', 'capacidade', 'localizacao', 'status', 'is_active',
            'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'telefone', 'cpf_cnpj', 'cep', 'endereco', 'numero',
            'complemento', 'bairro', 'cidade', 'estado', 'data_nascimento', 'observacoes',
            'is_active', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class ReservaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'cliente', 'cliente_nome', 'mesa', 'mesa_numero', 'data', 'horario',
            'quantidade_pessoas', 'status', 'observacoes', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'cliente_nome', 'mesa_numero', 'created_at', 'updated_at', 'loja_id']


class ItemPedidoSerializer(serializers.ModelSerializer):
    item_nome = serializers.CharField(source='item_cardapio.nome', read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 'pedido', 'item_cardapio', 'item_nome', 'quantidade', 'preco_unitario',
            'subtotal', 'observacoes', 'created_at'
        ]
        read_only_fields = ['id', 'item_nome', 'subtotal', 'created_at']


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    itens = ItemPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'numero_pedido', 'status', 'cliente', 'cliente_nome', 'mesa', 'mesa_numero',
            'tipo', 'subtotal', 'desconto', 'total', 'taxa_servico', 'taxa_entrega',
            'endereco_entrega', 'observacoes', 'itens', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = [
            'id', 'numero_pedido', 'cliente_nome', 'mesa_numero', 'itens',
            'created_at', 'updated_at', 'loja_id'
        ]


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'is_admin', 'is_active',
            'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = [
            'id', 'nome', 'cnpj', 'email', 'telefone', 'endereco', 'observacoes',
            'is_active', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class ItemNotaFiscalEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemNotaFiscalEntrada
        fields = [
            'id', 'nota_fiscal', 'descricao', 'quantidade', 'unidade',
            'valor_unitario', 'valor_total', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotaFiscalEntradaSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    itens = ItemNotaFiscalEntradaSerializer(many=True, read_only=True)

    class Meta:
        model = NotaFiscalEntrada
        fields = [
            'id', 'numero', 'fornecedor', 'fornecedor_nome', 'data_emissao', 'data_entrada',
            'valor_total', 'xml_file', 'observacoes', 'aplicado_estoque', 'itens',
            'is_active', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'fornecedor_nome', 'itens', 'created_at', 'updated_at', 'loja_id']


class EstoqueItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstoqueItem
        fields = [
            'id', 'nome', 'unidade', 'quantidade_atual', 'quantidade_minima',
            'observacoes', 'is_active', 'created_at', 'updated_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id']


class MovimentoEstoqueSerializer(serializers.ModelSerializer):
    estoque_item_nome = serializers.CharField(source='estoque_item.nome', read_only=True)

    class Meta:
        model = MovimentoEstoque
        fields = [
            'id', 'estoque_item', 'estoque_item_nome', 'quantidade', 'tipo',
            'nota_fiscal', 'observacao', 'created_at'
        ]
        read_only_fields = ['id', 'estoque_item_nome', 'created_at']


class RegistroPesoBalançaSerializer(serializers.ModelSerializer):
    estoque_item_nome = serializers.CharField(source='estoque_item.nome', read_only=True)

    class Meta:
        model = RegistroPesoBalança
        fields = [
            'id', 'estoque_item', 'estoque_item_nome', 'peso_kg', 'adicionar_ao_estoque',
            'observacao', 'created_at'
        ]
        read_only_fields = ['id', 'estoque_item_nome', 'created_at']
