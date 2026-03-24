"""
Mixins reutilizáveis para serializers
"""
from .phone_utils import normalizar_telefone


class PhoneNormalizationMixin:
    """
    Mixin para normalizar campos de telefone automaticamente
    
    Uso:
        class MeuSerializer(PhoneNormalizationMixin, serializers.ModelSerializer):
            phone_fields = ['telefone', 'phone', 'celular']  # Campos a normalizar
            
            class Meta:
                model = MeuModel
                fields = '__all__'
    
    Se não especificar phone_fields, normaliza campos padrão:
    - telefone
    - phone
    - celular
    - whatsapp
    - telefone_comercial
    - telefone_residencial
    """
    
    # Campos padrão a normalizar (pode ser sobrescrito na classe)
    phone_fields = [
        'telefone',
        'phone',
        'celular',
        'whatsapp',
        'telefone_comercial',
        'telefone_residencial',
        'owner_telefone',
    ]
    
    def validate(self, attrs):
        """
        Normaliza todos os campos de telefone antes de validar
        """
        # Obter lista de campos de telefone (da classe ou padrão)
        fields_to_normalize = getattr(self, 'phone_fields', self.phone_fields)
        
        # Normalizar cada campo de telefone presente nos dados
        for field_name in fields_to_normalize:
            if field_name in attrs and attrs[field_name]:
                attrs[field_name] = normalizar_telefone(attrs[field_name])
        
        # Chamar validação pai
        return super().validate(attrs)
    
    def to_representation(self, instance):
        """
        Garante que telefones sejam formatados na resposta também
        """
        data = super().to_representation(instance)
        
        # Obter lista de campos de telefone
        fields_to_normalize = getattr(self, 'phone_fields', self.phone_fields)
        
        # Normalizar cada campo de telefone na resposta
        for field_name in fields_to_normalize:
            if field_name in data and data[field_name]:
                data[field_name] = normalizar_telefone(data[field_name])
        
        return data
