"""Serializers de pacientes e anamnese."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfNormalizationMixin,
    TenantQuerysetMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Convenio, Patient, PatientAnamnese


class PatientSerializer(
    TenantQuerysetMixin,
    UniqueDocumentoPerLojaMixin,
    CpfNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    unique_documento_fields = ["cpf"]
    unique_documento_entidade = "paciente"
    unique_documento_apenas_ativos = True
    """Serializer para Pacientes. Aceita phone opcional e birth_date em YYYY-MM-DD ou DD/MM/YYYY."""
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"])
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.none(),
        required=False,
        allow_null=True,
    )
    convenio_name = serializers.SerializerMethodField()

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset("convenio", Convenio.objects.filter(is_active=True))

    phone_fields = ["phone", "telefone"]
    uppercase_fields = ["name", "nome", "cidade", "estado", "address", "endereco"]

    class Meta:
        model = Patient
        exclude = ["loja_id"]
        # Política de prazo é configurada só pelo admin, via endpoint dedicado
        # (PatientPrazoPagamentoView). Aqui é somente-leitura para exibir no prontuário.
        read_only_fields = [
            "prazo_pagamento_modo",
            "prazo_pagamento_dias",
            "prazo_pagamento_dia_mes",
        ]
        extra_kwargs = {
            "nome": {"required": True},
            "telefone": {"required": False, "allow_blank": True, "default": ""},
            "email": {"required": False, "allow_blank": True, "allow_null": True},
            "cpf": {"required": False, "allow_blank": True, "allow_null": True},
            "data_nascimento": {"required": False, "allow_null": True},
            "sexo": {"required": False, "allow_blank": True, "default": ""},
            "endereco": {"required": False, "allow_blank": True, "default": ""},
            "cidade": {"required": False, "allow_blank": True, "default": ""},
            "estado": {"required": False, "allow_blank": True, "default": ""},
            "observacoes": {"required": False, "allow_blank": True, "default": ""},
            "allow_whatsapp": {"required": False, "default": True},
            "address": {"required": False, "allow_blank": True, "allow_null": True},
            "notes": {"required": False, "allow_blank": True, "allow_null": True},
            "foto_url": {"required": False, "allow_blank": True, "default": ""},
        }

    def get_convenio_name(self, obj):
        if obj.convenio_id and obj.convenio:
            return obj.convenio.nome
        return "Particular"


class PatientPrazoPagamentoSerializer(serializers.ModelSerializer):
    """Política de prazo de pagamento do paciente (configurada só pelo admin).

    Valida a coerência entre o modo escolhido e o campo correspondente:
    - DIAS_APOS exige prazo_pagamento_dias.
    - DIA_FIXO exige prazo_pagamento_dia_mes.
    - '' (sem prazo) limpa os dois campos.
    """

    tem_prazo_pagamento = serializers.BooleanField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "prazo_pagamento_modo",
            "prazo_pagamento_dias",
            "prazo_pagamento_dia_mes",
            "tem_prazo_pagamento",
        ]
        read_only_fields = ["id", "tem_prazo_pagamento"]

    def validate(self, attrs):
        modo = attrs.get("prazo_pagamento_modo", getattr(self.instance, "prazo_pagamento_modo", ""))
        dias = attrs.get("prazo_pagamento_dias", getattr(self.instance, "prazo_pagamento_dias", None))
        dia_mes = attrs.get("prazo_pagamento_dia_mes", getattr(self.instance, "prazo_pagamento_dia_mes", None))

        if modo == Patient.PRAZO_MODO_DIAS_APOS:
            if not dias or int(dias) < 1:
                raise serializers.ValidationError(
                    {"prazo_pagamento_dias": "Informe a quantidade de dias após finalizar (mínimo 1)."},
                )
            attrs["prazo_pagamento_dia_mes"] = None
        elif modo == Patient.PRAZO_MODO_DIA_FIXO:
            if not dia_mes or not (1 <= int(dia_mes) <= 28):
                raise serializers.ValidationError(
                    {"prazo_pagamento_dia_mes": "Informe o dia fixo do mês (1 a 28)."},
                )
            attrs["prazo_pagamento_dias"] = None
        elif modo in ("", Patient.PRAZO_MODO_SEM):
            attrs["prazo_pagamento_modo"] = Patient.PRAZO_MODO_SEM
            attrs["prazo_pagamento_dias"] = None
            attrs["prazo_pagamento_dia_mes"] = None
        else:
            raise serializers.ValidationError({"prazo_pagamento_modo": "Modo de prazo inválido."})
        return attrs


class PatientAnamneseSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.nome", read_only=True)

    class Meta:
        model = PatientAnamnese
        fields = [
            "id", "patient", "patient_name",
            "queixa_principal", "historico_medico", "medicamentos_uso", "alergias",
            "condicoes_clinicas", "tipo_pele", "pressao_arterial", "peso", "altura",
            "observacoes", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "patient", "patient_name"]

    @staticmethod
    def _empty_decimal_to_none(value):
        if value in ("", None):
            return None
        return value

    def validate_peso(self, value):
        return self._empty_decimal_to_none(value)

    def validate_altura(self, value):
        return self._empty_decimal_to_none(value)
