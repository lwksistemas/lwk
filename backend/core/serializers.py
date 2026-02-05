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
        import logging
        from tenants.middleware import get_current_loja_id
        
        logger = logging.getLogger(__name__)
        loja_id = get_current_loja_id()
        
        logger.info(f"[BaseLojaSerializer.create] Tentando criar {self.Meta.model.__name__} - loja_id={loja_id}")
        logger.info(f"[BaseLojaSerializer.create] validated_data keys: {list(validated_data.keys())}")
        
        if not loja_id:
            logger.error(f"[BaseLojaSerializer.create] ERRO: loja_id não encontrado no contexto!")
            logger.error(f"[BaseLojaSerializer.create] Model: {self.Meta.model.__name__}")
            logger.error(f"[BaseLojaSerializer.create] Data: {validated_data}")
            
            raise serializers.ValidationError({
                'detail': 'Contexto da loja não identificado. Recarregue a página e tente novamente.',
                'error_code': 'LOJA_CONTEXT_MISSING',
                'model': self.Meta.model.__name__
            })
        
        validated_data['loja_id'] = loja_id
        logger.info(f"[BaseLojaSerializer.create] Criando {self.Meta.model.__name__} com loja_id={loja_id}")
        
        return super().create(validated_data)
