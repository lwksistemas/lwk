"""Serializers de orçamento de consulta."""
from rest_framework import serializers


class OrcamentoItemInputSerializer(serializers.Serializer):
    procedure_id = serializers.IntegerField()
    valor_customizado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    quantidade = serializers.IntegerField(min_value=1, default=1)
    observacao_item = serializers.CharField(required=False, allow_blank=True, default="")


class OrcamentoCreateSerializer(serializers.Serializer):
    consulta_id = serializers.IntegerField()
    itens = OrcamentoItemInputSerializer(many=True)
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")
    validade_dias = serializers.IntegerField(min_value=1, max_value=365, default=30)

    def validate_itens(self, value):
        if not value:
            raise serializers.ValidationError("Informe ao menos um item.")
        return value


class OrcamentoStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ACEITO", "RECUSADO"])
