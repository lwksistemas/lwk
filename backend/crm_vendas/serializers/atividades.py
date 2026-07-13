"""Serializers de atividades CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    TextNormalizationMixin,
)

from ..models import Atividade


class AtividadeSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['titulo']
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)
    
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'conta', 'conta_nome',
            'data', 'duracao_minutos',
            'concluido', 'observacoes', 'google_event_id', 'created_at', 'updated_at',
            'lembrete_whatsapp', 'lembrete_whatsapp_telefone',
            'lembrete_24h_enviado_em', 'lembrete_2h_enviado_em',
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'lembrete_24h_enviado_em', 'lembrete_2h_enviado_em',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lembrete = attrs.get(
            'lembrete_whatsapp',
            getattr(self.instance, 'lembrete_whatsapp', False) if self.instance else False,
        )
        telefone = attrs.get('lembrete_whatsapp_telefone')
        if telefone is None and self.instance:
            telefone = self.instance.lembrete_whatsapp_telefone
        if lembrete and not (telefone or '').strip():
            raise serializers.ValidationError({
                'lembrete_whatsapp_telefone': 'Informe o WhatsApp para lembretes automáticos.',
            })
        return attrs

    def update(self, instance, validated_data):
        nova_data = validated_data.get('data')
        if nova_data is not None and nova_data != instance.data:
            validated_data['lembrete_24h_enviado_em'] = None
            validated_data['lembrete_2h_enviado_em'] = None
        if validated_data.get('lembrete_whatsapp') is False:
            validated_data.setdefault('lembrete_whatsapp_telefone', '')
        return super().update(instance, validated_data)


class AtividadeListSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    """Serializer para listagem sem google_event_id (compatível com schemas antigos)."""
    uppercase_fields = ['titulo']
    conta_nome = serializers.SerializerMethodField()
    lead_nome = serializers.SerializerMethodField()
    
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'lead_nome', 'conta', 'conta_nome',
            'data', 'duracao_minutos',
            'concluido', 'observacoes', 'created_at', 'updated_at',
            'lembrete_whatsapp', 'lembrete_whatsapp_telefone',
        ]

    def get_lead_nome(self, obj):
        if obj.lead_id and getattr(obj, 'lead', None):
            return (obj.lead.nome or '').strip()
        return ''

    def get_conta_nome(self, obj):
        try:
            return obj.conta.nome if obj.conta else None
        except Exception:
            return None

