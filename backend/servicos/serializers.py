from rest_framework import serializers
from core.serializer_mixins import TextNormalizationMixin, CpfCnpjNormalizationMixin
from .models import Categoria, Servico, Cliente, Profissional, Agendamento, OrdemServico, Orcamento, Funcionario


class CategoriaSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome']
    phone_fields = []

    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    uppercase_fields = ['nome']
    phone_fields = []

    class Meta:
        model = Servico
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ClienteSerializer(CpfCnpjNormalizationMixin, TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome', 'cidade', 'estado', 'bairro']
    phone_fields = ['telefone']
    cpf_cnpj_fields = ['cpf_cnpj']

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ProfissionalSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome', 'especialidade']
    phone_fields = ['telefone']

    class Meta:
        model = Profissional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AgendamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)

    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OrdemServicoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)

    class Meta:
        model = OrdemServico
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OrcamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)

    class Meta:
        model = Orcamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class FuncionarioSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome', 'cargo']
    phone_fields = ['telefone']

    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
