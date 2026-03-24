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


class UpperCaseNormalizationMixin:
    """
    Mixin para converter campos de texto para MAIÚSCULAS automaticamente
    
    Uso:
        class MeuSerializer(UpperCaseNormalizationMixin, serializers.ModelSerializer):
            uppercase_fields = ['nome', 'empresa', 'cidade']  # Campos a converter
            
            class Meta:
                model = MeuModel
                fields = '__all__'
    
    Se não especificar uppercase_fields, converte campos padrão:
    - nome
    - name
    - empresa
    - razao_social
    - cidade
    - estado
    - bairro
    - cargo
    """
    
    # Campos padrão a converter (pode ser sobrescrito na classe)
    uppercase_fields = [
        'nome',
        'name',
        'empresa',
        'razao_social',
        'cidade',
        'estado',
        'bairro',
        'cargo',
        'especialidade',
        'segmento',
    ]
    
    def validate(self, attrs):
        """
        Converte campos de texto para maiúsculas antes de validar
        """
        # Obter lista de campos (da classe ou padrão)
        fields_to_uppercase = getattr(self, 'uppercase_fields', self.uppercase_fields)
        
        # Converter cada campo presente nos dados
        for field_name in fields_to_uppercase:
            if field_name in attrs and attrs[field_name]:
                # Converter para string e depois para maiúsculas
                value = str(attrs[field_name]).strip()
                if value:
                    attrs[field_name] = value.upper()
        
        # Chamar validação pai
        return super().validate(attrs)
    
    def to_representation(self, instance):
        """
        Garante que campos sejam maiúsculas na resposta também
        """
        data = super().to_representation(instance)
        
        # Obter lista de campos
        fields_to_uppercase = getattr(self, 'uppercase_fields', self.uppercase_fields)
        
        # Converter cada campo na resposta
        for field_name in fields_to_uppercase:
            if field_name in data and data[field_name]:
                value = str(data[field_name]).strip()
                if value:
                    data[field_name] = value.upper()
        
        return data


class TextNormalizationMixin(PhoneNormalizationMixin, UpperCaseNormalizationMixin):
    """
    Mixin combinado que normaliza telefones E converte texto para maiúsculas
    
    Uso:
        class MeuSerializer(TextNormalizationMixin, serializers.ModelSerializer):
            phone_fields = ['telefone']  # Campos de telefone
            uppercase_fields = ['nome', 'empresa']  # Campos para maiúsculas
            
            class Meta:
                model = MeuModel
                fields = '__all__'
    
    Este mixin combina:
    - PhoneNormalizationMixin: Formata telefones
    - UpperCaseNormalizationMixin: Converte texto para maiúsculas
    """
    pass
