"""Serializer de retry de emails."""
from rest_framework import serializers

from ..models import EmailRetry

class EmailRetrySerializer(serializers.ModelSerializer):
    """
    Serializer para EmailRetry
    
    ✅ NOVO v719: Gerenciamento de emails com falha de envio
    """
    
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    loja_slug = serializers.CharField(source='loja.slug', read_only=True)
    pode_retentar = serializers.SerializerMethodField()
    atingiu_max = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailRetry
        fields = [
            'id',
            'destinatario',
            'assunto',
            'mensagem',
            'tentativas',
            'max_tentativas',
            'enviado',
            'erro',
            'loja',
            'loja_nome',
            'loja_slug',
            'created_at',
            'updated_at',
            'proxima_tentativa',
            'pode_retentar',
            'atingiu_max',
            'status_display',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_pode_retentar(self, obj):
        """Verifica se ainda pode tentar reenviar"""
        return obj.pode_retentar()
    
    def get_atingiu_max(self, obj):
        """Verifica se atingiu máximo de tentativas"""
        return obj.atingiu_max_tentativas()
    
    def get_status_display(self, obj):
        """Retorna status formatado"""
        if obj.enviado:
            return "✅ Enviado"
        elif obj.atingiu_max_tentativas():
            return f"❌ Falhou ({obj.tentativas}/{obj.max_tentativas})"
        else:
            return f"⏳ Aguardando ({obj.tentativas}/{obj.max_tentativas})"


