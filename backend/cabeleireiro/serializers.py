from rest_framework import serializers

from core.serializer_mixins import (
    CpfNormalizationMixin,
    TenantQuerysetMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from .models import Agendamento, Cliente, Profissional, Servico


class ClienteSerializer(
    TenantQuerysetMixin,
    UniqueDocumentoPerLojaMixin,
    CpfNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    """Alinhado ao PatientSerializer da clínica (aliases phone/birth_date/notes)."""

    unique_documento_fields = ["cpf"]
    unique_documento_entidade = "cliente"
    unique_documento_apenas_ativos = True
    phone_fields = ["phone", "telefone"]
    uppercase_fields = ["name", "nome", "cidade", "estado", "logradouro", "bairro", "endereco"]

    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"],
    )

    class Meta:
        model = Cliente
        exclude = ["loja_id"]
        extra_kwargs = {
            "nome": {"required": True},
            "telefone": {"required": False, "allow_blank": True, "default": ""},
            "email": {"required": False, "allow_blank": True, "allow_null": True},
            "cpf": {"required": False, "allow_blank": True, "allow_null": True},
            "data_nascimento": {"required": False, "allow_null": True},
            "endereco": {"required": False, "allow_blank": True, "default": ""},
            "cidade": {"required": False, "allow_blank": True, "default": ""},
            "estado": {"required": False, "allow_blank": True, "default": ""},
            "observacoes": {"required": False, "allow_blank": True, "default": ""},
            "allow_whatsapp": {"required": False, "default": True},
            "foto_url": {"required": False, "allow_blank": True, "default": ""},
            "cep": {"required": False, "allow_blank": True, "default": ""},
            "logradouro": {"required": False, "allow_blank": True, "default": ""},
            "numero": {"required": False, "allow_blank": True, "default": ""},
            "complemento": {"required": False, "allow_blank": True, "default": ""},
            "bairro": {"required": False, "allow_blank": True, "default": ""},
        }

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if data.get("birth_date") and not data.get("data_nascimento"):
            data["data_nascimento"] = data.get("birth_date")
        if data.get("notes") is not None and data.get("observacoes") is None:
            data["observacoes"] = data.get("notes")
        if data.get("name") and not data.get("nome"):
            data["nome"] = data.get("name")
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["phone"] = instance.telefone or ""
        data["birth_date"] = instance.data_nascimento.isoformat() if instance.data_nascimento else None
        data["notes"] = instance.observacoes or ""
        data["name"] = instance.nome
        return data


class ProfissionalSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome", "especialidade"]

    class Meta:
        model = Profissional
        exclude = ["loja_id"]


class ServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome", "categoria"]

    class Meta:
        model = Servico
        exclude = ["loja_id"]


class AgendamentoSerializer(TenantQuerysetMixin, serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    profissional_nome = serializers.SerializerMethodField()
    servico_nome = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    def get_profissional_nome(self, obj):
        return obj.profissional.nome if obj.profissional_id else ""

    def get_servico_nome(self, obj):
        return obj.servico.nome if obj.servico_id else ""

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset("cliente", Cliente.objects.filter(is_active=True))
        self.bind_tenant_queryset("profissional", Profissional.objects.filter(is_active=True))
        self.bind_tenant_queryset("servico", Servico.objects.filter(is_active=True))

    class Meta:
        model = Agendamento
        exclude = ["loja_id"]
        read_only_fields = ["created_at", "updated_at"]
