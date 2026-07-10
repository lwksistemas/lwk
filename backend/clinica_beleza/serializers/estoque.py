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
    # _base_manager: evita falso "Pk inválido" quando o isolation filter
    # ainda não enxerga a categoria no momento da validação do import XML.
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaEstoque._base_manager.all(),
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

    def _resolve_loja_id(self):
        request = self.context.get('request')
        loja_id = self.context.get('loja_id')
        if loja_id:
            return loja_id
        if request:
            loja_id = resolve_loja_id_from_request(request)
            if loja_id:
                return loja_id
        from tenants.middleware import get_current_loja_id
        return get_current_loja_id()

    def to_internal_value(self, data):
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        if mutable.get('validade') in ('', None):
            mutable['validade'] = None

        loja_id = self._resolve_loja_id()
        cat_raw = mutable.get('categoria')
        cat_id_raw = mutable.pop('categoria_id', None) if 'categoria_id' in mutable else None

        # Preferir slug; ID só se existir nesta loja
        if isinstance(cat_raw, str) and cat_raw.strip() and not cat_raw.strip().isdigit():
            cat = resolver_categoria(loja_id=loja_id, slug=normalizar_slug_categoria(cat_raw))
            if cat:
                mutable['categoria'] = cat.pk
            else:
                mutable.pop('categoria', None)
        else:
            pk = None
            if cat_id_raw not in (None, ''):
                try:
                    pk = int(cat_id_raw)
                except (TypeError, ValueError):
                    pk = None
            elif isinstance(cat_raw, str) and cat_raw.strip().isdigit():
                pk = int(cat_raw.strip())
            elif isinstance(cat_raw, int):
                pk = cat_raw

            slug_hint = None
            if isinstance(mutable.get('categoria_slug'), str):
                slug_hint = mutable.get('categoria_slug')

            cat = resolver_categoria(loja_id=loja_id, categoria_id=pk, slug=slug_hint or 'outro')
            if cat:
                mutable['categoria'] = cat.pk
            else:
                mutable.pop('categoria', None)

        return super().to_internal_value(mutable)

    def validate_categoria(self, value):
        if value is None:
            return value
        loja_id = self._resolve_loja_id()
        if loja_id and getattr(value, 'loja_id', None) not in (None, loja_id):
            raise serializers.ValidationError('Categoria não pertence a esta loja.')
        return value

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
