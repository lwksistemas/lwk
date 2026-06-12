"""
Mixins reutilizáveis para serializers
"""
from rest_framework import serializers

from .phone_utils import telefone_exibicao_brasileiro, telefone_internacional_br
from .cpf_utils import (
    documento_preenchido,
    existe_documento_duplicado,
    mensagem_documento_duplicado,
    normalizar_cpf,
    normalizar_cpf_cnpj,
)


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
    - owner_telefone
    - whatsapp_numero
    - telefone_whatsapp
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
        'whatsapp_numero',
        'telefone_whatsapp',
    ]
    
    def validate(self, attrs):
        """
        Normaliza telefones para formato internacional BR (55 + DDD + número).
        """
        fields_to_normalize = getattr(self, 'phone_fields', self.phone_fields)
        
        for field_name in fields_to_normalize:
            if field_name in attrs and attrs[field_name]:
                attrs[field_name] = telefone_internacional_br(attrs[field_name])
        
        return super().validate(attrs)
    
    def to_representation(self, instance):
        """
        Exibe telefones no formato brasileiro (DD) XXXXX-XXXX.
        """
        data = super().to_representation(instance)
        
        fields_to_normalize = getattr(self, 'phone_fields', self.phone_fields)
        
        for field_name in fields_to_normalize:
            if field_name in data and data[field_name]:
                data[field_name] = telefone_exibicao_brasileiro(data[field_name])
        
        return data


class CpfNormalizationMixin:
    """
    Mixin para padronizar campos de CPF automaticamente no formato XXX.XXX.XXX-XX.

    Uso:
        class MeuSerializer(CpfNormalizationMixin, serializers.ModelSerializer):
            cpf_fields = ['cpf']  # Campos a normalizar (padrão: ['cpf'])
    """

    cpf_fields = ['cpf']

    def validate(self, attrs):
        fields_to_normalize = getattr(self, 'cpf_fields', self.cpf_fields)
        for field_name in fields_to_normalize:
            if field_name in attrs and attrs[field_name]:
                attrs[field_name] = normalizar_cpf(attrs[field_name])
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        fields_to_normalize = getattr(self, 'cpf_fields', self.cpf_fields)
        for field_name in fields_to_normalize:
            if field_name in data and data[field_name]:
                data[field_name] = normalizar_cpf(data[field_name])
        return data


class CpfCnpjNormalizationMixin:
    """
    Mixin para padronizar campos de CPF/CNPJ automaticamente.
    - CPF (11 dígitos): XXX.XXX.XXX-XX
    - CNPJ (14 dígitos): XX.XXX.XXX/XXXX-XX

    Uso:
        class MeuSerializer(CpfCnpjNormalizationMixin, serializers.ModelSerializer):
            cpf_cnpj_fields = ['cpf_cnpj']  # Campos a normalizar (padrão: ['cpf_cnpj'])
    """

    cpf_cnpj_fields = ['cpf_cnpj']

    def validate(self, attrs):
        fields_to_normalize = getattr(self, 'cpf_cnpj_fields', self.cpf_cnpj_fields)
        for field_name in fields_to_normalize:
            if field_name in attrs and attrs[field_name]:
                attrs[field_name] = normalizar_cpf_cnpj(attrs[field_name])
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        fields_to_normalize = getattr(self, 'cpf_cnpj_fields', self.cpf_cnpj_fields)
        for field_name in fields_to_normalize:
            if field_name in data and data[field_name]:
                data[field_name] = normalizar_cpf_cnpj(data[field_name])
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


class UniqueDocumentoPerLojaMixin:
    """
    Impede CPF/CNPJ/documento duplicado no mesmo cadastro (por loja ou global).

    Uso:
        class PatientSerializer(UniqueDocumentoPerLojaMixin, ...):
            unique_documento_fields = ['cpf']
            unique_documento_entidade = 'paciente'
    """

    unique_documento_fields: list[str] = []
    unique_documento_entidade: str = "cadastro"
    unique_documento_global: bool = False
    unique_documento_apenas_ativos: bool = False

    def _validar_documento_unico(self, field_name: str, value):
        if not documento_preenchido(value):
            return value

        model = getattr(getattr(self, "Meta", None), "model", None)
        if model is None:
            return value

        loja_id = None
        if not self.unique_documento_global:
            from tenants.middleware import get_current_loja_id

            loja_id = get_current_loja_id()
            if not loja_id:
                return value

        exclude_pk = self.instance.pk if self.instance else None
        if existe_documento_duplicado(
            model=model,
            field_name=field_name,
            value=value,
            loja_id=loja_id,
            exclude_pk=exclude_pk,
            escopo_global=self.unique_documento_global,
            apenas_ativos=self.unique_documento_apenas_ativos,
        ):
            raise serializers.ValidationError(
                mensagem_documento_duplicado(
                    field_name,
                    escopo_global=self.unique_documento_global,
                    entidade=self.unique_documento_entidade,
                )
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        fields = getattr(self, "unique_documento_fields", None) or []
        for field_name in fields:
            if field_name not in attrs:
                continue
            self._validar_documento_unico(field_name, attrs[field_name])
        return attrs


class TenantQuerysetMixin:
    """
    Reatribui querysets de PrimaryKeyRelatedField na instanciação do serializer.

    Querysets definidos no corpo da classe são avaliados na importação do módulo,
    sem contexto de tenant — LojaIsolationManager retorna vazio e a validação de PK falha.
    """

    def bind_tenant_queryset(self, field_name, queryset):
        field = self.fields.get(field_name)
        if field is not None:
            field.queryset = queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply = getattr(self, 'apply_tenant_querysets', None)
        if callable(apply):
            apply()


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
