"""Serializers de configuração de retorno gratuito."""
from rest_framework import serializers

from core.serializer_mixins import TenantQuerysetMixin

from ..models import AgendaRetornoConfig, Procedure, RetornoProcedimentoRegra


class AgendaRetornoConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaRetornoConfig
        fields = [
            "id",
            "retorno_procedimento_ativo",
            "retorno_consulta_ativo",
            "dias_retorno_consulta",
            "created_at",
            "updated_at",
            "loja_id",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]

    def validate_dias_retorno_consulta(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Informe pelo menos 1 dia.")
        if value is not None and value > 3650:
            raise serializers.ValidationError("Prazo máximo: 3650 dias.")
        return value


class RetornoProcedimentoRegraSerializer(TenantQuerysetMixin, serializers.ModelSerializer):
    procedure_name = serializers.CharField(source="procedure.nome", read_only=True)

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset("procedure", Procedure.objects.filter(is_active=True))

    class Meta:
        model = RetornoProcedimentoRegra
        fields = [
            "id",
            "procedure",
            "procedure_name",
            "dias_retorno",
            "is_active",
            "created_at",
            "updated_at",
            "loja_id",
        ]
        read_only_fields = ["created_at", "updated_at", "loja_id"]

    def validate(self, attrs):
        procedure = attrs.get("procedure")
        loja_id = self.context.get("loja_id")
        if procedure and loja_id:
            from tenants.middleware import get_current_loja_id
            lid = loja_id or get_current_loja_id()
            qs = RetornoProcedimentoRegra.objects.filter(
                loja_id=lid, procedure=procedure, is_active=True,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "procedure": "Já existe regra de retorno para este procedimento.",
                })
        return attrs

    def validate_dias_retorno(self, value):
        if value < 1:
            raise serializers.ValidationError("Informe pelo menos 1 dia.")
        if value > 3650:
            raise serializers.ValidationError("Prazo máximo: 3650 dias.")
        return value
