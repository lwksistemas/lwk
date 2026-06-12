"""Serializers de procedimentos e protocolos."""
from rest_framework import serializers
from core.serializer_mixins import TextNormalizationMixin

from ..models import Procedure, ProcedureProtocol


class ProcedureSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome']
    phone_fields = []

    class Meta:
        model = Procedure
        exclude = ['loja_id']
        extra_kwargs = {
            'categoria': {'required': False, 'allow_blank': True, 'default': ''},
        }


class ProcedureProtocolSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    procedure_categoria = serializers.CharField(source='procedure.categoria', read_only=True)

    class Meta:
        model = ProcedureProtocol
        exclude = ['loja_id']
        extra_kwargs = {
            'descricao': {'required': False, 'allow_blank': True},
            'preparacao': {'required': False, 'allow_blank': True},
            'execucao': {'required': False, 'allow_blank': True},
            'pos_procedimento': {'required': False, 'allow_blank': True},
            'materiais_necessarios': {'required': False, 'allow_blank': True},
            'contraindicacoes': {'required': False, 'allow_blank': True},
            'cuidados_especiais': {'required': False, 'allow_blank': True},
        }
