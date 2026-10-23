"""Serializers de catálogo produtos/serviços."""
from rest_framework import serializers

from core.serializer_mixins import (
    TextNormalizationMixin,
)

from ..models import CategoriaProdutoServico, ProdutoServico


def cadeia_categoria(categoria):
    nos = []
    atual = categoria
    for _ in range(6):
        if atual is None:
            break
        nos.append(atual)
        atual = atual.pai
    nos.reverse()
    return nos


class CategoriaProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()
    caminho = serializers.SerializerMethodField()
    uppercase_fields = ["nome"]

    class Meta:
        model = CategoriaProdutoServico
        fields = [
            "id", "nome", "descricao", "cor", "ordem", "ativo", "pai",
            "caminho", "produtos_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "caminho"]

    def get_produtos_count(self, obj):
        """Retorna quantidade de produtos/serviços nesta categoria"""
        return obj.produtos_servicos.filter(ativo=True).count()

    def get_caminho(self, obj):
        return [item.nome for item in cadeia_categoria(obj)]

    def validate_pai(self, pai):
        if pai is None:
            return pai
        atual = pai
        for _ in range(6):
            if atual is None:
                break
            if self.instance is not None and atual.pk == self.instance.pk:
                raise serializers.ValidationError("A subpasta não pode ficar dentro dela mesma.")
            atual = atual.pai
        return pai


class ProdutoServicoResumoSerializer(serializers.ModelSerializer):
    """Campos do seletor da oportunidade, sem percorrer a árvore de pastas."""

    categoria_nome = serializers.SerializerMethodField()
    categoria_cor = serializers.SerializerMethodField()

    class Meta:
        model = ProdutoServico
        fields = ["id", "tipo", "codigo", "nome", "preco", "categoria", "categoria_nome", "categoria_cor"]

    def get_categoria_nome(self, obj):
        categoria = getattr(obj, "categoria", None)
        return categoria.nome if categoria is not None else ""

    def get_categoria_cor(self, obj):
        categoria = getattr(obj, "categoria", None)
        return categoria.cor if categoria is not None else ""


class ProdutoServicoSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)
    categoria_cor = serializers.CharField(source="categoria.cor", read_only=True)
    categoria_caminho = serializers.SerializerMethodField()
    prestadora_nome = serializers.SerializerMethodField()
    uppercase_fields = ["nome", "codigo"]

    class Meta:
        model = ProdutoServico
        fields = [
            "id", "tipo", "codigo", "nome", "descricao", "categoria",
            "categoria_nome", "categoria_cor", "categoria_caminho", "prestadora", "prestadora_nome",
            "preco", "recorrencia", "ativo",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_categoria_caminho(self, obj):
        if not getattr(obj, "categoria_id", None):
            return []
        return [item.nome for item in cadeia_categoria(obj.categoria)]

    def get_prestadora_nome(self, obj):
        conta = getattr(obj, "prestadora", None)
        if conta is None:
            return ""
        return conta.nome or conta.razao_social or ""

    def validate_prestadora(self, conta):
        if conta is None:
            return conta
        if conta.tipo not in ("prestadora", "ambos"):
            raise serializers.ValidationError("Escolha uma prestadora.")
        loja_id = getattr(self.instance, "loja_id", None)
        if loja_id and conta.loja_id != loja_id:
            raise serializers.ValidationError("A prestadora não é desta loja.")
        return conta
