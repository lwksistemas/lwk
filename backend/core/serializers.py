"""
Serializers genéricos para evitar duplicação de código
"""
from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Serializer genérico para modelos base
    """
    class Meta:
        fields = '__all__'
    
    def validate(self, data):
        """Validações customizadas podem ser adicionadas aqui"""
        return data


class TimestampedSerializer(serializers.ModelSerializer):
    """
    Serializer que inclui campos de timestamp formatados
    """
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        fields = '__all__'
    
    def get_created_at_formatted(self, obj):
        """Retorna data de criação formatada"""
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y %H:%M')
        return None
    
    def get_updated_at_formatted(self, obj):
        """Retorna data de atualização formatada"""
        if obj.updated_at:
            return obj.updated_at.strftime('%d/%m/%Y %H:%M')
        return None