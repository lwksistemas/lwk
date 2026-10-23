"""Serializers de contas CRM."""
from django.db import transaction
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..comissao_prestadora_service import (
    TIPOS_COM_COMISSAO,
    aplicar_comissoes_conta,
    serializar_comissoes_conta,
)
from ..models import Conta


class ContaSerializer(
    CpfCnpjNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    cpf_cnpj_fields = ["cnpj"]
    unique_documento_fields = ["cnpj"]
    unique_documento_entidade = "empresa"
    phone_fields = ["telefone"]
    uppercase_fields = ["nome", "razao_social", "segmento", "cidade", "bairro", "uf"]

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    site = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    comissoes = serializers.JSONField(required=False, write_only=True)
    logo = serializers.URLField(required=False, allow_blank=True, max_length=500)
    comissao_valor = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True,
    )

    class Meta:
        model = Conta
        fields = [
            "id", "nome", "razao_social", "cnpj", "inscricao_estadual", "tipo", "segmento",
            "telefone", "email", "site",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "endereco", "observacoes", "logo",
            "comissao_escopo", "comissao_tipo", "comissao_valor",
            "comissoes", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_email(self, value):
        if not value or value.strip() == "":
            return None
        return value

    def validate_site(self, value):
        if not value or value.strip() == "":
            return None
        return value

    def validate_logo(self, value):
        if not value or not str(value).strip():
            return ""
        return str(value).strip()

    def validate(self, attrs):
        escopo = attrs.get("comissao_escopo", getattr(self.instance, "comissao_escopo", "especificos"))
        tipo = attrs.get("comissao_tipo", getattr(self.instance, "comissao_tipo", "percentual"))
        valor = attrs.get("comissao_valor", getattr(self.instance, "comissao_valor", None))
        if escopo not in ("todos", "especificos"):
            raise serializers.ValidationError({"comissao_escopo": "Escolha todos os serviços ou só alguns."})
        if tipo not in ("percentual", "fixo"):
            raise serializers.ValidationError({"comissao_tipo": "Escolha porcentagem ou valor fixo."})
        if valor is not None and valor < 0:
            raise serializers.ValidationError({"comissao_valor": "A comissão não pode ser negativa."})
        if tipo == "percentual" and valor is not None and valor > 100:
            raise serializers.ValidationError({"comissao_valor": "A porcentagem não pode passar de 100."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        from ..utils import vendedor_nao_ve_valor_da_prestadora

        if request and vendedor_nao_ve_valor_da_prestadora(request):
            data.pop("comissoes", None)
            data.pop("comissao_escopo", None)
            data.pop("comissao_tipo", None)
            data.pop("comissao_valor", None)
            return data
        view = self.context.get("view")
        if getattr(view, "action", None) in ("retrieve", "create", "update", "partial_update"):
            data["comissoes"] = serializar_comissoes_conta(instance)
        return data

    def _gravar_comissoes(self, instance, comissoes):
        request = self.context.get("request")
        from ..utils import vendedor_nao_ve_valor_da_prestadora

        if request and vendedor_nao_ve_valor_da_prestadora(request):
            return
        if comissoes is None and instance.tipo in TIPOS_COM_COMISSAO:
            return
        aplicar_comissoes_conta(instance, [] if comissoes is None else comissoes)

    @transaction.atomic
    def create(self, validated_data):
        comissoes = validated_data.pop("comissoes", None)
        instance = super().create(validated_data)
        self._gravar_comissoes(instance, comissoes)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        comissoes = validated_data.pop("comissoes", None)
        instance = super().update(instance, validated_data)
        self._gravar_comissoes(instance, comissoes)
        return instance

