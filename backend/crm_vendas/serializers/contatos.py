"""Serializers de contatos CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Contato

class ContatoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'cargo']

    class Meta:
        model = Contato
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'conta', 'conta_nome',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

