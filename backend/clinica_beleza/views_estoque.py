"""
Views de Estoque — Clínica da Beleza
Controle de produtos (botox, ácido hialurônico, soros, etc.)
"""
import logging
from decimal import Decimal

from django.db.models import F, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ProdutoEstoque, MovimentacaoEstoque
from .serializers import ProdutoEstoqueSerializer, MovimentacaoEstoqueSerializer
from .views_base import GetObjectMixin

logger = logging.getLogger(__name__)


class ProdutoEstoqueListView(APIView):
    """
    GET /clinica-beleza/estoque/
    POST /clinica-beleza/estoque/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ProdutoEstoque.objects.all().order_by('nome')
        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        apenas_ativos = request.query_params.get('active', 'true').lower() == 'true'
        if apenas_ativos:
            qs = qs.filter(is_active=True)
        estoque_baixo = request.query_params.get('estoque_baixo')
        if estoque_baixo == 'true':
            qs = qs.filter(quantidade_atual__lte=F('quantidade_minima'))
        return Response(ProdutoEstoqueSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ProdutoEstoqueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProdutoEstoqueDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/estoque/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProdutoEstoqueSerializer(obj).data)

    def put(self, request, pk):
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
    permission_classes = [IsAuthenticated]
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


class HistoricoEstoqueView(GetObjectMixin, APIView):
    """
    GET /clinica-beleza/estoque/<id>/historico/
    Retorna histórico de movimentações do produto.
    """
    permission_classes = [IsAuthenticated]
    model_class = ProdutoEstoque
    not_found_message = 'Produto não encontrado'

    def get(self, request, pk):
        produto, error = self.object_or_404(pk)
        if error:
            return error
        movs = MovimentacaoEstoque.objects.filter(
            produto=produto
        ).select_related('profissional').order_by('-created_at')[:50]
        return Response({
            'produto': produto.nome,
            'movimentacoes': MovimentacaoEstoqueSerializer(movs, many=True).data,
        })


class EstoqueResumoView(APIView):
    """
    GET /clinica-beleza/estoque/resumo/
    Resumo: total produtos, estoque baixo, valor total.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
