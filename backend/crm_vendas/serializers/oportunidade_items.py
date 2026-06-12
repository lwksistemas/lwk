"""Serializer de itens de oportunidade."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import OportunidadeItem

class OportunidadeItemSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    produto_servico_nome = serializers.CharField(source='produto_servico.nome', read_only=True)
    produto_servico_tipo = serializers.CharField(source='produto_servico.tipo', read_only=True)
    produto_servico_recorrencia = serializers.CharField(source='produto_servico.recorrencia', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OportunidadeItem
        fields = [
            'id', 'oportunidade', 'produto_servico', 'produto_servico_nome', 'produto_servico_tipo',
            'produto_servico_recorrencia',
            'quantidade', 'preco_unitario', 'subtotal', 'observacao', 'created_at',
        ]
        read_only_fields = ['created_at']

    def get_subtotal(self, obj):
        return float(obj.quantidade * obj.preco_unitario)

