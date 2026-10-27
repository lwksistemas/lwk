"""Serializers de procedimentos e protocolos."""
from decimal import Decimal

from rest_framework import serializers

from core.serializer_mixins import TextNormalizationMixin

from ..models import (
    CategoriaProcedimento,
    Procedure,
    ProcedureProtocol,
    ProdutoEstoque,
    ProtocoloProcedimento,
    ProtocoloProduto,
)


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


class _ProtocoloProcedimentoInputSerializer(serializers.Serializer):
    procedure = serializers.IntegerField()
    desconto_tipo = serializers.CharField(required=False, allow_blank=True, default="")
    desconto_valor = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal("0.00"))


class ProcedureProtocolSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source="procedure.nome", read_only=True)
    procedure_categoria = serializers.CharField(source="procedure.categoria", read_only=True)
    produtos = _ProtocoloProdutoInputSerializer(many=True, required=False, write_only=True)
    procedimentos = _ProtocoloProcedimentoInputSerializer(many=True, required=False, write_only=True)

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
            "desconto_escopo": {"required": False},
            "desconto_tipo": {"required": False, "allow_blank": True},
            "desconto_valor": {"required": False},
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

    def validate(self, attrs):
        escopo = (attrs.get("desconto_escopo") or getattr(self.instance, "desconto_escopo", "total") or "total").strip().lower()
        if escopo not in ("total", "individual"):
            raise serializers.ValidationError({"desconto_escopo": "Escolha desconto no total ou em cada procedimento."})
        attrs["desconto_escopo"] = escopo
        tipo = (attrs.get("desconto_tipo") if "desconto_tipo" in attrs else getattr(self.instance, "desconto_tipo", "percentual") or "").strip().lower()
        valor = attrs.get("desconto_valor", getattr(self.instance, "desconto_valor", Decimal("0.00")))
        valor = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
        if escopo == "total":
            if tipo not in ("percentual", "fixo"):
                tipo = "percentual"
            if valor < 0:
                raise serializers.ValidationError({"desconto_valor": "O desconto não pode ser negativo."})
            if tipo == "percentual" and valor > 100:
                raise serializers.ValidationError({"desconto_valor": "A porcentagem do desconto fica entre 0 e 100."})
            attrs["desconto_tipo"] = tipo
            attrs["desconto_valor"] = valor
        else:
            attrs["desconto_tipo"] = "percentual"
            attrs["desconto_valor"] = Decimal("0.00")
        if "procedimentos" in attrs:
            attrs["procedimentos"] = self._validar_procedimentos(attrs["procedimentos"], escopo)
        return attrs

    def _validar_procedimentos(self, value, escopo):
        vistos = set()
        for linha in value:
            procedure_id = linha["procedure"]
            if procedure_id in vistos:
                raise serializers.ValidationError({"procedimentos": "Procedimento repetido na promoção."})
            vistos.add(procedure_id)
            if not Procedure.objects.filter(pk=procedure_id, is_active=True).exists():
                raise serializers.ValidationError({"procedimentos": "Procedimento não encontrado."})
            tipo = (linha.get("desconto_tipo") or "").strip().lower()
            desconto = Decimal(str(linha.get("desconto_valor") or 0)).quantize(Decimal("0.01"))
            if escopo == "individual":
                if tipo not in ("", "percentual", "fixo"):
                    raise serializers.ValidationError({"procedimentos": "Escolha desconto em reais ou em porcentagem."})
                if desconto < 0:
                    raise serializers.ValidationError({"procedimentos": "O desconto não pode ser negativo."})
                if tipo == "percentual" and desconto > 100:
                    raise serializers.ValidationError({"procedimentos": "A porcentagem do desconto fica entre 0 e 100."})
                if tipo not in ("percentual", "fixo"):
                    tipo = ""
                    desconto = Decimal("0.00")
                linha["desconto_tipo"] = tipo
                linha["desconto_valor"] = desconto
            else:
                linha["desconto_tipo"] = ""
                linha["desconto_valor"] = Decimal("0.00")
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
        minutos = int(getattr(instance.procedure, "duracao_minutos", 0) or 0)
        if minutos > 0:
            data["tempo_estimado"] = minutos
        data["procedimentos"] = [
            {
                "id": linha.id,
                "procedure": linha.procedure_id,
                "nome": linha.procedure.nome,
                "preco": str(linha.procedure.preco),
                "categoria": linha.procedure.categoria,
                "desconto_tipo": linha.desconto_tipo or "percentual",
                "desconto_valor": str(linha.desconto_valor),
            }
            for linha in instance.itens.all()
        ]
        return data

    def _usar_duracao_do_procedimento(self, validated_data, instance=None):
        procedure = validated_data.get("procedure", getattr(instance, "procedure", None))
        if procedure is None:
            return
        minutos = int(getattr(procedure, "duracao_minutos", 0) or 0)
        validated_data["tempo_estimado"] = minutos if minutos > 0 else 30

    def create(self, validated_data):
        produtos = validated_data.pop("produtos", [])
        procedimentos = validated_data.pop("procedimentos", [])
        self._usar_duracao_do_procedimento(validated_data)
        protocolo = super().create(validated_data)
        _gravar_produtos_protocolo(protocolo, produtos)
        _gravar_procedimentos_protocolo(protocolo, procedimentos)
        return protocolo

    def update(self, instance, validated_data):
        produtos = validated_data.pop("produtos", serializers.empty)
        procedimentos = validated_data.pop("procedimentos", serializers.empty)
        self._usar_duracao_do_procedimento(validated_data, instance)
        protocolo = super().update(instance, validated_data)
        if produtos is not serializers.empty:
            protocolo.produtos.all().delete()
            _gravar_produtos_protocolo(protocolo, produtos)
        if procedimentos is not serializers.empty:
            protocolo.itens.all().delete()
            _gravar_procedimentos_protocolo(protocolo, procedimentos)
        return protocolo


def _gravar_procedimentos_protocolo(protocolo, procedimentos) -> None:
    for ordem, linha in enumerate(procedimentos):
        ProtocoloProcedimento.objects.create(
            protocol=protocolo,
            procedure_id=linha["procedure"],
            desconto_tipo=linha.get("desconto_tipo") or "",
            desconto_valor=linha.get("desconto_valor") or Decimal("0.00"),
            ordem=ordem,
            loja_id=protocolo.loja_id,
        )


def _gravar_produtos_protocolo(protocolo, produtos) -> None:
    for linha in produtos:
        ProtocoloProduto.objects.create(
            protocol=protocolo,
            produto_id=linha["produto"],
            quantidade=linha["quantidade"],
            loja_id=protocolo.loja_id,
        )
