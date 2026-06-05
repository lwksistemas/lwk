"""Serializers de convênios e locais de atendimento."""
from rest_framework import serializers

from ..models import Convenio, ConvenioProcedimentoPreco, LocalAtendimento


class ConvenioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convenio
        fields = ['id', 'nome', 'codigo', 'is_active']


class ConvenioPrecoSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    preco_particular = serializers.DecimalField(
        source='procedure.preco', max_digits=10, decimal_places=2, read_only=True,
    )
    preco_efetivo = serializers.SerializerMethodField()

    class Meta:
        model = ConvenioProcedimentoPreco
        fields = [
            'id', 'procedure', 'procedure_name', 'preco_particular',
            'modo', 'preco', 'preco_efetivo',
        ]

    def get_preco_efetivo(self, obj):
        return float(obj.calcular_preco_efetivo())


class ConvenioSerializer(serializers.ModelSerializer):
    precos = serializers.SerializerMethodField()

    class Meta:
        model = Convenio
        fields = ['id', 'nome', 'codigo', 'is_active', 'precos', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_precos(self, obj):
        rows = obj.precos_procedimentos.filter(is_active=True).select_related('procedure')
        return ConvenioPrecoSerializer(rows, many=True).data

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('O nome do convênio é obrigatório.')
        return value.strip()


class LocalAtendimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalAtendimento
        fields = ['id', 'nome', 'valor_consulta', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('O nome do local é obrigatório.')
        return value.strip()

    def validate_valor_consulta(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('O valor deve ser maior ou igual a zero.')
        return value
