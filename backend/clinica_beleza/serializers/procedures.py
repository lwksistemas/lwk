"""Serializers de procedimentos e protocolos."""
from decimal import Decimal

from rest_framework import serializers

from core.serializer_mixins import TextNormalizationMixin

from ..models import CategoriaProcedimento, Procedure, ProcedureProtocol, ProdutoEstoque, ProtocoloProduto


class CategoriaProcedimentoSerializer(serializers.ModelSerializer):
    procedimentos_count = serializers.IntegerField(read_only=True, required=False, default=0)

    class Meta:
        model = CategoriaProcedimento
        exclude = ["loja_id"]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def validate_nome(self, value):
        nome = (value or "").strip()
        if not nome:
            raise serializers.ValidationError("Nome é obrigatório.")
        return nome


class ProcedureSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ["nome"]
    phone_fields = []

    class Meta:
        model = Procedure
        exclude = ["loja_id"]
        extra_kwargs = {
            "categoria": {"required": False, "allow_blank": True, "default": ""},
        }


class _ProtocoloProdutoInputSerializer(serializers.Serializer):
    produto = serializers.IntegerField()
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=2)


class ProcedureProtocolSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source="procedure.nome", read_only=True)
    procedure_categoria = serializers.CharField(source="procedure.categoria", read_only=True)
    produtos = _ProtocoloProdutoInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = ProcedureProtocol
        exclude = ["loja_id"]
        extra_kwargs = {
            "descricao": {"required": False, "allow_blank": True},
            "preparacao": {"required": False, "allow_blank": True},
            "execucao": {"required": False, "allow_blank": True},
            "pos_procedimento": {"required": False, "allow_blank": True},
            "materiais_necessarios": {"required": False, "allow_blank": True},
            "contraindicacoes": {"required": False, "allow_blank": True},
            "cuidados_especiais": {"required": False, "allow_blank": True},
            "sessoes": {"required": False, "min_value": 1},
            "intervalo_quantidade": {"required": False, "min_value": 1},
            "intervalo_unidade": {"required": False},
            "valor": {"required": False},
        }

    def validate_valor(self, value):
        if value is None:
            return Decimal("0.00")
        if value < 0:
            raise serializers.ValidationError("O valor do protocolo não pode ser negativo.")
        return value

    def validate_intervalo_unidade(self, value):
        if value not in ("dias", "semanas", "meses"):
            raise serializers.ValidationError("Escolha dias, semanas ou meses.")
        return value

    def validate_produtos(self, value):
        vistos = set()
        for linha in value:
            produto_id = linha["produto"]
            if produto_id in vistos:
                raise serializers.ValidationError("Produto repetido no protocolo.")
            vistos.add(produto_id)
            if linha["quantidade"] <= 0:
                raise serializers.ValidationError("A quantidade por sessão precisa ser maior que zero.")
            if not ProdutoEstoque.objects.filter(pk=produto_id, is_active=True).exists():
                raise serializers.ValidationError("Produto não encontrado.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["produtos"] = [
            {
                "id": linha.id,
                "produto": linha.produto_id,
                "quantidade": str(linha.quantidade),
                "produto_nome": linha.produto.nome,
                "unidade_medida": linha.produto.unidade_medida,
            }
            for linha in instance.produtos.all()
        ]
        return data

    def create(self, validated_data):
        produtos = validated_data.pop("produtos", [])
        protocolo = super().create(validated_data)
        _gravar_produtos_protocolo(protocolo, produtos)
        return protocolo

    def update(self, instance, validated_data):
        produtos = validated_data.pop("produtos", serializers.empty)
        protocolo = super().update(instance, validated_data)
        if produtos is not serializers.empty:
            protocolo.produtos.all().delete()
            _gravar_produtos_protocolo(protocolo, produtos)
        return protocolo


def _gravar_produtos_protocolo(protocolo, produtos) -> None:
    for linha in produtos:
        ProtocoloProduto.objects.create(
            protocol=protocolo,
            produto_id=linha["produto"],
            quantidade=linha["quantidade"],
            loja_id=protocolo.loja_id,
        )
