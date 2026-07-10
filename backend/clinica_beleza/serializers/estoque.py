"""Serializers de estoque."""
from rest_framework import serializers

from ..models import ConsultaProdutoUtilizado, MovimentacaoEstoque, ProdutoEstoque
from ..models.estoque import CategoriaEstoque
from ..estoque_categorias import normalizar_slug_categoria, resolver_categoria
from ..views_base import resolve_loja_id_from_request


class CategoriaEstoqueSerializer(serializers.ModelSerializer):
    produtos_count = serializers.IntegerField(read_only=True, required=False, default=0)

    class Meta:
        model = CategoriaEstoque
        exclude = ['loja_id']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def validate_nome(self, value):
        nome = (value or '').strip()
        if not nome:
            raise serializers.ValidationError('Nome é obrigatório.')
        return nome


class ProdutoEstoqueSerializer(serializers.ModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaEstoque.objects.all(),
        allow_null=True,
        required=False,
    )
    categoria_slug = serializers.CharField(source='categoria.slug', read_only=True, default='outro')
    categoria_display = serializers.CharField(source='categoria.nome', read_only=True, default='Outro')
    categoria_cor = serializers.CharField(source='categoria.cor', read_only=True, default='#8B3D52')
    estoque_baixo = serializers.BooleanField(read_only=True)
    validade = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = ProdutoEstoque
        exclude = ['loja_id']

    def to_internal_value(self, data):
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        if mutable.get('validade') in ('', None):
            mutable['validade'] = None

        # Aceita categoria como id, slug string, ou categoria_id
        cat_raw = mutable.get('categoria')
        if 'categoria_id' in mutable and mutable.get('categoria_id') not in (None, ''):
            cat_raw = mutable.pop('categoria_id')

        if isinstance(cat_raw, str) and cat_raw.strip() and not cat_raw.strip().isdigit():
            request = self.context.get('request')
            loja_id = resolve_loja_id_from_request(request) if request else None
            if not loja_id:
                from tenants.middleware import get_current_loja_id
                loja_id = get_current_loja_id()
            cat = resolver_categoria(loja_id=loja_id, slug=normalizar_slug_categoria(cat_raw))
            if cat:
                mutable['categoria'] = cat.pk
            else:
                mutable.pop('categoria', None)
        elif isinstance(cat_raw, str) and cat_raw.strip().isdigit():
            mutable['categoria'] = int(cat_raw.strip())

        return super().to_internal_value(mutable)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.categoria_id:
            data['categoria'] = None
            data['categoria_slug'] = 'outro'
            data['categoria_display'] = 'Outro'
            data['categoria_cor'] = '#8B3D52'
        return data


class ConsultaProdutoUtilizadoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    unidade_medida = serializers.CharField(source='produto.unidade_medida', read_only=True)
    quantidade_disponivel = serializers.DecimalField(
        source='produto.quantidade_atual', max_digits=10, decimal_places=2, read_only=True,
    )

    class Meta:
        model = ConsultaProdutoUtilizado
        exclude = ['loja_id']
        read_only_fields = ['estoque_baixado', 'created_at']


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(
        source='profissional.nome', read_only=True, default=None,
    )

    class Meta:
        model = MovimentacaoEstoque
        exclude = ['loja_id']
