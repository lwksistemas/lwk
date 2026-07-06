"""Serializer de notas de negociação da oportunidade."""
from rest_framework import serializers

from core.serializer_mixins import TextNormalizationMixin

from ..models import OportunidadeNota


class OportunidadeNotaSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    tipo_label = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = OportunidadeNota
        fields = [
            'id', 'oportunidade', 'tipo', 'tipo_label', 'texto',
            'autor_nome', 'created_at',
        ]
        read_only_fields = ['id', 'autor_nome', 'created_at', 'tipo_label']

    def validate_texto(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('Informe o texto da nota.')
        return value.strip()
