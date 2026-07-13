"""Serializers de convênios e locais de atendimento."""
from rest_framework import serializers

from core.serializer_mixins import TextNormalizationMixin

from ..models import Convenio, ConvenioProcedimentoPreco, LocalAtendimento, NomeAgenda


class ConvenioListSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome"]
    phone_fields = []

    class Meta:
        model = Convenio
        fields = ["id", "nome", "codigo", "is_active"]


class ConvenioPrecoSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source="procedure.nome", read_only=True)
    preco_particular = serializers.DecimalField(
        source="procedure.preco", max_digits=10, decimal_places=2, read_only=True,
    )
    preco_efetivo = serializers.SerializerMethodField()

    class Meta:
        model = ConvenioProcedimentoPreco
        fields = [
            "id", "procedure", "procedure_name", "preco_particular",
            "modo", "preco", "preco_efetivo",
        ]

    def get_preco_efetivo(self, obj):
        return float(obj.calcular_preco_efetivo())


def gerar_codigo_convenio(convenio):
    """Código único gerado após criar o convênio (ex.: CV00042)."""
    return f"CV{convenio.id:05d}"


class ConvenioSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    precos = serializers.SerializerMethodField()
    uppercase_fields = ["nome"]
    phone_fields = []

    class Meta:
        model = Convenio
        fields = ["id", "nome", "codigo", "is_active", "precos", "created_at", "updated_at"]
        read_only_fields = ["id", "codigo", "created_at", "updated_at"]

    def get_precos(self, obj):
        rows = obj.precos_procedimentos.filter(is_active=True).select_related("procedure")
        return ConvenioPrecoSerializer(rows, many=True).data

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O nome do convênio é obrigatório.")
        return value.strip()

    def create(self, validated_data):
        convenio = super().create(validated_data)
        convenio.codigo = gerar_codigo_convenio(convenio)
        convenio.save(update_fields=["codigo", "updated_at"])
        return convenio


class LocalAtendimentoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome"]
    phone_fields = []
    class Meta:
        model = LocalAtendimento
        fields = [
            "id", "nome", "valor_consulta", "tempo_consulta_minutos",
            "is_padrao", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O nome do local é obrigatório.")
        return value.strip()

    def validate_valor_consulta(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError("O valor deve ser maior ou igual a zero.")
        return value

    def validate_tempo_consulta_minutos(self, value):
        if value is None:
            return value
        if value < 1 or value > 480:
            raise serializers.ValidationError("O tempo deve ser entre 1 e 480 minutos.")
        return value


class NomeAgendaSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome"]
    phone_fields = []

    class Meta:
        model = NomeAgenda
        fields = ["id", "nome", "is_padrao", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O nome da agenda é obrigatório.")
        return value.strip()
