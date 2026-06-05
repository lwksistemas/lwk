"""Serializers de pacientes e anamnese."""
from rest_framework import serializers

from ..models import Convenio, Patient, PatientAnamnese
from core.serializer_mixins import TextNormalizationMixin, CpfNormalizationMixin


class PatientSerializer(CpfNormalizationMixin, TextNormalizationMixin, serializers.ModelSerializer):
    """Serializer para Pacientes. Aceita phone opcional e birth_date em YYYY-MM-DD ou DD/MM/YYYY."""
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'])
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    convenio_name = serializers.SerializerMethodField()

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
            'observacoes', 'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']
