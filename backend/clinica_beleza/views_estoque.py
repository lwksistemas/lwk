"""
Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
from decimal import Decimal

from django.db.models import F, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_ESTOQUE, CLINICA_MEMBER
from rest_framework import status

from .models import ProdutoEstoque, MovimentacaoEstoque
from .serializers import ProdutoEstoqueSerializer, MovimentacaoEstoqueSerializer
from .pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .views_base import GetObjectMixin

# Campos para listagem via .values() (inclui numero_nota desde migration 0034).
_PRODUTO_VALUES_FIELDS = (
    'id', 'nome', 'categoria', 'marca', 'unidade_medida',
    'quantidade_atual', 'quantidade_minima', 'preco_custo', 'preco_venda',
    'validade', 'lote', 'numero_nota', 'observacoes', 'is_active', 'created_at', 'updated_at',
)
_CATEGORIA_LABELS = dict(ProdutoEstoque.CATEGORIA_CHOICES)


def _produto_values_row(row: dict) -> dict:
    item = dict(row)
    item.setdefault('numero_nota', '')
    item['categoria_display'] = _CATEGORIA_LABELS.get(row.get('categoria'), row.get('categoria'))
    item['estoque_baixo'] = row.get('quantidade_atual', 0) <= row.get('quantidade_minima', 0)
    return item


def _paginate_produtos_values(queryset, request):
    """Lista produtos via .values()."""
    page_param = request.query_params.get('page')
    if page_param is None:
        rows = list(queryset.values(*_PRODUTO_VALUES_FIELDS))
        return Response([_produto_values_row(r) for r in rows])

    try:
        page = max(1, int(page_param))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(
            MAX_PAGE_SIZE,
            max(1, int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))),
        )
    except (ValueError, TypeError):
        page_size = DEFAULT_PAGE_SIZE

    total = queryset.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    rows = list(queryset.values(*_PRODUTO_VALUES_FIELDS)[offset:offset + page_size])
    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': [_produto_values_row(r) for r in rows],
    })


class ProdutoEstoqueListView(APIView):
    """
    GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """
    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        # Profissionais em consulta precisam listar insumos; gestão continua restrita.
        if self.request.method == 'GET':
            return [perm() for perm in CLINICA_MEMBER]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        qs = ProdutoEstoque.objects.all().order_by('nome')
        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        search = (request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(nome__icontains=search)
        apenas_ativos = request.query_params.get('active', 'true').lower() == 'true'
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get('estoque_baixo')
        if estoque_baixo == 'true':
            qs = qs.filter(quantidade_atual__lte=F('quantidade_minima'))
        # Sempre via .values() para resposta leve na listagem.
        return _paginate_produtos_values(qs, request)

    def post(self, request):
        serializer = ProdutoEstoqueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [perm() for perm in CLINICA_MEMBER]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProdutoEstoqueSerializer(obj).data)

    def put(self, request, pk):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = ProdutoEstoqueSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MovimentacaoEstoqueView(GetObjectMixin, APIView):
    """
    POST /clinica-beleza/estoque/<id>/movimentar/
    Registra entrada ou saída de estoque e atualiza quantidade.
    Body: { "tipo": "entrada"|"saida"|"ajuste", "quantidade": 5, "motivo": "Compra fornecedor" }
    """
    permission_classes = CLINICA_ESTOQUE
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

    def post(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error

        tipo = request.data.get('tipo', '').strip()
        if tipo not in ('entrada', 'saida', 'ajuste'):
            return Response({'error': 'Tipo deve ser: entrada, saida ou ajuste'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantidade = Decimal(str(request.data.get('quantidade', 0)))
            if quantidade <= 0:
                return Response({'error': 'Quantidade deve ser maior que zero'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Quantidade inválida'}, status=status.HTTP_400_BAD_REQUEST)

        motivo = (request.data.get('motivo') or '').strip()
        profissional_id = request.data.get('profissional_id')
        appointment_id = request.data.get('appointment_id')

        # Atualizar quantidade
        if tipo == 'entrada':
            produto.quantidade_atual += quantidade
        elif tipo == 'saida':
            if produto.quantidade_atual < quantidade:
                return Response(
                    {'error': f'Estoque insuficiente. Disponível: {produto.quantidade_atual} {produto.unidade_medida}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            produto.quantidade_atual -= quantidade
        elif tipo == 'ajuste':
            produto.quantidade_atual = quantidade

        produto.save(update_fields=['quantidade_atual', 'updated_at'])

        # Registrar movimentação
        mov = MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            motivo=motivo,
            profissional_id=profissional_id,
            appointment_id=appointment_id,
        )

        return Response({
            'id': mov.id,
            'produto': produto.nome,
            'tipo': tipo,
            'quantidade': float(quantidade),
            'quantidade_atual': float(produto.quantidade_atual),
            'estoque_baixo': produto.estoque_baixo,
        })


class EstoqueResumoView(APIView):
    """
    GET /clinica-beleza/estoque/resumo/
    Resumo: total produtos, estoque baixo, valor total.
    """
    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from tenants.middleware import ensure_loja_context

        ensure_loja_context(request)
        produtos = ProdutoEstoque.objects.filter(is_active=True)
        total_produtos = produtos.count()
        estoque_baixo = produtos.filter(quantidade_atual__lte=F('quantidade_minima')).count()
        valor_total = produtos.aggregate(
            total=Sum(F('quantidade_atual') * F('preco_custo'))
        )['total'] or 0

        return Response({
            'total_produtos': total_produtos,
            'estoque_baixo': estoque_baixo,
            'valor_total_estoque': float(valor_total),
        })
