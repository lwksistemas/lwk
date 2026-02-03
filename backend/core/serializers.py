"""
Serializers base para evitar duplicação de código
"""
from rest_framework import serializers


class BaseLojaSerializer(serializers.ModelSerializer):
    """
    Serializer base que adiciona loja_id automaticamente no create().
    
    Todos os modelos que usam LojaIsolationMixin devem herdar deste serializer
    para garantir que loja_id seja preenchido automaticamente do contexto.
    
    Uso:
        class ClienteSerializer(BaseLojaSerializer):
            class Meta:
                model = Cliente
                fields = '__all__'
                read_only_fields = ['created_at', 'updated_at', 'loja_id']
    """
    
    def create(self, validated_data):
        """
        Adiciona loja_id automaticamente do contexto da requisição.
        
        Falha explicitamente se o contexto da loja não estiver definido,
        evitando criação de registros sem isolamento.
        """
        from tenants.middleware import get_current_loja_id
        
        loja_id = get_current_loja_id()
        if not loja_id:
            raise serializers.ValidationError({
                'loja_id': 'Contexto da loja não identificado. Recarregue a página e tente novamente.'
            })
        
        validated_data['loja_id'] = loja_id
        return super().create(validated_data)
