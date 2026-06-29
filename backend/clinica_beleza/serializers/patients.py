"""Serializers de pacientes e anamnese."""
from rest_framework import serializers

from ..models import Convenio, Patient, PatientAnamnese
from core.serializer_mixins import (
    CpfNormalizationMixin,
    TenantQuerysetMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)


class PatientSerializer(
    TenantQuerysetMixin,
    UniqueDocumentoPerLojaMixin,
    CpfNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    unique_documento_fields = ['cpf']
    unique_documento_entidade = 'paciente'
    unique_documento_apenas_ativos = True
    """Serializer para Pacientes. Aceita phone opcional e birth_date em YYYY-MM-DD ou DD/MM/YYYY."""
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'])
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.none(),
        required=False,
        allow_null=True,
    )
    convenio_name = serializers.SerializerMethodField()

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset('convenio', Convenio.objects.filter(is_active=True))

    phone_fields = ['phone', 'telefone']
    uppercase_fields = ['name', 'nome', 'cidade', 'estado', 'address', 'endereco']

    class Meta:
        model = Patient
        exclude = ['loja_id']
        extra_kwargs = {
            'nome': {'required': True},
            'telefone': {'required': False, 'allow_blank': True, 'default': ''},
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'cpf': {'required': False, 'allow_blank': True, 'allow_null': True},
            'data_nascimento': {'required': False, 'allow_null': True},
            'endereco': {'required': False, 'allow_blank': True, 'default': ''},
            'cidade': {'required': False, 'allow_blank': True, 'default': ''},
            'estado': {'required': False, 'allow_blank': True, 'default': ''},
            'observacoes': {'required': False, 'allow_blank': True, 'default': ''},
            'allow_whatsapp': {'required': False, 'default': True},
            'address': {'required': False, 'allow_blank': True, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
            'foto_url': {'required': False, 'allow_blank': True, 'default': ''},
        }

    def get_convenio_name(self, obj):
        if obj.convenio_id and obj.convenio:
            return obj.convenio.nome
        return 'Particular'


class PatientAnamneseSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)

    class Meta:
        model = PatientAnamnese
        fields = [
            'id', 'patient', 'patient_name',
            'queixa_principal', 'historico_medico', 'medicamentos_uso', 'alergias',
            'condicoes_clinicas', 'tipo_pele', 'pressao_arterial', 'peso', 'altura',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'patient', 'patient_name']

    @staticmethod
    def _empty_decimal_to_none(value):
        if value in ('', None):
            return None
        return value

    def validate_peso(self, value):
        return self._empty_decimal_to_none(value)

    def validate_altura(self, value):
        return self._empty_decimal_to_none(value)
